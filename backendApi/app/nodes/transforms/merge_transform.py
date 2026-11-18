import itertools
import os
import traceback
from typing import Dict, Iterator, List, Optional, Any, Tuple

from pydantic import BaseModel, ConfigDict, TypeAdapter
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.transforms.transform_node import TransformNode
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import logging

from app.utils.security import PathSecurityValidator

from app.config.settings import settings

logger = logging.getLogger(__name__)

from app.utils.utils import generate_pandas_schema
class Source(BaseModel):
    id: str
    name: str
    type: str
    datasetId: str

class DataMappingItem(BaseModel):
    id: str
    sources: List[Source]
    targetName: str

# Number of rows of the batches of the merge with the parquet option
BATCH_SIZE = 100


def _to_arrow(column: pd.Series) -> pa.Array:
    """Arrow array of a pandas column; a categorical column gives its values, not their codes."""
    array = pa.Array.from_pandas(column)
    if pa.types.is_dictionary(array.type):
        array = array.dictionary_decode()
    return array


def _column_type(column: pd.Series) -> pa.DataType:
    """Arrow type of a pandas column: only an object column needs its values to tell its type."""
    return _to_arrow(column if column.dtype == object else column.iloc[:0]).type


def _column_chunks(column: pd.Series) -> Iterator[pa.Array]:
    """Yield a pandas column by chunks."""
    for start in range(0, len(column), BATCH_SIZE):
        yield _to_arrow(column.iloc[start:start + BATCH_SIZE])


def _common_type(target_name: str, types: List[pa.DataType]) -> pa.DataType:
    """Type that holds the values of every source of a target column (an integer and a float give a float).

    Raises:
        ValueError: If the types cannot be stored in one parquet column, as a number and a text.
    """
    try:
        schemas = [pa.schema([pa.field(target_name, source_type)]) for source_type in types]
        return pa.unify_schemas(schemas, promote_options="permissive").field(0).type
    except (pa.ArrowInvalid, pa.ArrowTypeError) as e:
        names = ', '.join(str(source_type) for source_type in types)
        raise ValueError(f"The sources of column '{target_name}' have types that cannot be merged in a parquet file: {names}") from e


def _batches(chunks: Iterator[pa.Array], size: int) -> Iterator[pa.Array]:
    """Regroup the chunks, put end to end, in batches of the given size (the last one may be shorter)."""
    pending = None
    for chunk in chunks:
        pending = chunk if pending is None else pa.concat_arrays([pending, chunk])
        while len(pending) >= size:
            yield pending.slice(0, size)
            pending = pending.slice(size)
    if pending is not None and len(pending) > 0:
        yield pending


def _completed(array: Optional[pa.Array], array_type: pa.DataType, size: int) -> pa.Array:
    """The array completed with nulls up to the given size; None stands for a column that has no more values."""
    if array is None:
        return pa.nulls(size, array_type)
    if len(array) < size:
        return pa.concat_arrays([array, pa.nulls(size - len(array), array_type)])
    return array


class MergeTransform(TransformNode):

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new ExampleTransform instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    

    def process(self, sample=False) -> StatusNode:
        """
        Processes the input data by merging columns from different sources based on a predefined mapping.
        Args:
            sample (bool, optional): If True, use sample data for processing. Defaults to False.
        Returns:
            StatusNode: The status of the node after processing. Returns StatusNode.Valid if successful, 
                        otherwise returns StatusNode.Error.
        Raises:
            ValueError: If the input data format  is not handle.

        """
        try:
            # Retrieve the data mapping
            data_mapping, parquet_save = self._retreiveColumnsMapping()

            if parquet_save:
                return self.process_if_parquet(data_mapping, sample)

            combined_df = self._merge_in_memory(data_mapping, sample)
        except Exception as e:
            return self._fail(e)

        return self._publish_dataframe(combined_df, "Merged Data", sample)

    def _merge_in_memory(self, data_mapping, sample: bool) -> pd.DataFrame:
        """One column per mapping item, concatenating the columns of its sources.

        A column shorter than the longest one is completed with missing values.
        """
        columns = {}
        for mapping_item in data_mapping:
            # Sort sources by their order in the mapping item to ensure to keep the same order for all columns
            sorted_sources = sorted(mapping_item.sources, key=lambda x: x.id)
            column_data = [column for column in (self._source_column(source, sample) for source in sorted_sources)
                           if column is not None]
            # Concatenate all the column data
            if column_data:
                columns[mapping_item.targetName] = pd.concat(column_data, ignore_index=True)
        if not columns:
            return pd.DataFrame()
        # The columns are aligned on their row numbers: no row of the longest one is lost
        return pd.concat(columns, axis=1)

    def _source_column(self, source: Source, sample: bool) -> Optional[pd.Series]:
        """The column of a source, or None if its dataset is not an input of the node."""
        dataset_id = source.datasetId
        column_name = source.name
        if dataset_id not in self.inputs:
            return None
        source_df = self.inputs[dataset_id].get_node_data()
        if isinstance(source_df, NodeDataPandasDf):
            frame = source_df.dataExample if sample else source_df.data
            return frame[column_name]
        if isinstance(source_df, NodeDataParquet):
            # Read the Parquet file and extract the specified column
            file_path = PathSecurityValidator.validate_file_path(source_df.data)
            return pq.read_table(file_path, columns=[column_name]).to_pandas()[column_name]
        raise ValueError(f"Input data {dataset_id} is not a handled format")
    
    def process_if_parquet(self, data_mapping, sample = False) -> StatusNode:
        """
        Processes the input data by merging columns from different sources based on a predefined mapping.
        Uses parquet file and batch processing to reduce memory usage.

        The file holds the same rows as the in-memory merge: each target column holds its sources end to end,
        and a column shorter than the longest one is completed with missing values.
        """
        # One stream of batches per target column
        columns = {}
        for mapping_item in data_mapping:
            column = self._target_column(mapping_item, sample)
            if column is not None:
                columns[mapping_item.targetName] = column
        schema = pa.schema([pa.field(name, column_type) for name, (column_type, _) in columns.items()])

        secure_path = os.path.join(settings.upload_dir, f"merged_data_{self.id}.parquet")
        parquet_path = PathSecurityValidator.validate_file_path(secure_path)

        # Process data in batches: the file is always written, even without any row
        with pq.ParquetWriter(parquet_path, schema) as parquet_writer:
            for arrays in itertools.zip_longest(*(batches for _, batches in columns.values())):
                parquet_writer.write_table(self._aligned_table(arrays, schema))

        # Create the node data output
        parquet_file = pq.ParquetFile(parquet_path)
        node_data = NodeDataParquet(
            data=parquet_path,
            nodeSchema=parquet_file.schema,
            name="merged_data",
        )
        self.outputs.get('out').set_node_data(node_data, self)
        return StatusNode.Valid

    def _target_column(self, mapping_item: DataMappingItem, sample: bool) -> Optional[Tuple[pa.DataType, Iterator[pa.Array]]]:
        """Type and batches of a target column, or None if no dataset of its sources is an input of the node."""
        # Sort sources by their order in the mapping item to ensure to keep the same order for all columns
        sorted_sources = sorted(mapping_item.sources, key=lambda x: x.id)
        sources = [self._open_source(source, sample) for source in sorted_sources if source.datasetId in self.inputs]
        if not sources:
            return None
        column_type = _common_type(mapping_item.targetName, [source_type for source_type, _ in sources])
        chunks = (chunk.cast(column_type) for _, source_chunks in sources for chunk in source_chunks)
        return column_type, _batches(chunks, BATCH_SIZE)

    def _open_source(self, source: Source, sample: bool) -> Tuple[pa.DataType, Iterator[pa.Array]]:
        """Type of the column of a source, and its values by chunks (read when the chunks are consumed)."""
        source_data = self.inputs[source.datasetId].get_node_data()
        if isinstance(source_data, NodeDataPandasDf):
            df = source_data.dataExample if sample else source_data.data
            column = df[source.name]
            return _column_type(column), _column_chunks(column)
        if isinstance(source_data, NodeDataParquet):
            file_path = PathSecurityValidator.validate_file_path(source_data.data)
            parquet_file = pq.ParquetFile(file_path)
            column_type = parquet_file.schema_arrow.field(source.name).type
            # Read by batches, whatever the size of the row groups of the file
            batches = parquet_file.iter_batches(batch_size=BATCH_SIZE, columns=[source.name])
            return column_type, (batch.column(0) for batch in batches)
        raise TypeError("Unkown input type")

    @staticmethod
    def _aligned_table(arrays, schema: pa.Schema) -> pa.Table:
        """Table of one batch: a column that is shorter than the longest one, or finished, is completed with nulls."""
        size = max(len(array) for array in arrays if array is not None)
        return pa.Table.from_arrays(
            [_completed(array, field.type, size) for array, field in zip(arrays, schema)], schema=schema)

    def _retreiveColumnsMapping(self) -> tuple[List[DataMappingItem], bool]:
        if self.data.get('dataMapping') and self.data.get('parquetSave'):
            mappings = TypeAdapter(List[DataMappingItem]).validate_python(self.data.get('dataMapping'))
            parquet_save = self.data.get('parquetSave')['value']
            return mappings, parquet_save
        else:
            raise ValueError("Data Mapping is required")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )