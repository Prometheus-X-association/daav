import asyncio
import traceback
from typing import Any, Iterator, Literal, Optional

import pandas as pd
import pyarrow.parquet as pq
from pydantic import ConfigDict

from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import ElasticDataset, _validate_es_index
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.outputs.output_node import OutputNode
from app.services.dataset_service import DatasetService
from app.services.elastic_service import ElasticService, infer_mappings
from app.utils import utils

CHUNK_SIZE = 1000


class ElasticOutput(OutputNode):

    datasetService: Optional[DatasetService] = None
    elasticService: Optional[ElasticService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new ElasticOutput instance.

        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)
        self.datasetService = DatasetService()
        self.elasticService = ElasticService()

    async def process(self, sample=False) -> StatusNode:
        """Index the input data into an Elasticsearch index.

        Args:
            sample (bool): Flag to indicate if process on sample should be done. Defaults to False.

        Returns:
            StatusNode: The status of the node after processing.
        """
        try:
            dataset, index, if_exist, id_field = await self._retrieveParams()
            indexed = await asyncio.to_thread(self._write, dataset, index, if_exist, id_field, sample)
            self.statusMessage = f"{indexed} documents indexed into '{index}'"
        except Exception as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error
        return StatusNode.Valid

    def _chunks(self, sample: bool) -> Iterator[pd.DataFrame]:
        """Yield the connected input data as DataFrame chunks."""
        for data in self._connected_data():
            yield from self._data_chunks(data, sample)

    def _data_chunks(self, data: Any, sample: bool) -> Iterator[pd.DataFrame]:
        """Yield the data of one input as DataFrame chunks."""
        if isinstance(data, NodeDataPandasDf):
            yield from utils.slice_generator(self._input_dataframe(data, sample), CHUNK_SIZE)
        elif isinstance(data, NodeDataParquet):
            yield from self._parquet_chunks(data.data, sample)
        else:
            raise TypeError("Unsupported data type: {}".format(type(data)))

    @staticmethod
    def _parquet_chunks(path: str, sample: bool) -> Iterator[pd.DataFrame]:
        """Yield a parquet file by batches; a sample only yields the first batch."""
        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches(batch_size=CHUNK_SIZE):
            yield batch.to_pandas()
            if sample:
                break

    def _write(self, dataset: ElasticDataset, index: str, if_exist: str, id_field: Optional[str], sample: bool) -> int:
        chunks = self._chunks(sample)
        first = next(chunks, None)
        if first is None:
            raise ValueError("No input data connected")
        if id_field and id_field not in first.columns:
            raise ValueError(f"The id field '{id_field}' is not a column of the input data")

        indexed, failed, errors = 0, 0, []
        with self.elasticService.connect(dataset) as client:
            exists = bool(client.indices.exists(index=index))
            if exists and if_exist == 'fail':
                raise ValueError(f"Index '{index}' already exists and ifExist is set to 'fail'")
            if exists and if_exist == 'replace':
                client.indices.delete(index=index)
                exists = False
            if not exists:
                client.indices.create(index=index, mappings=infer_mappings(first))

            for chunk in (first, *chunks):
                ok, ko, errs = self.elasticService.bulk_index(
                    client, index, chunk.to_dict(orient='records'), id_field=id_field
                )
                indexed += ok
                failed += ko
                errors.extend(errs[:max(0, 5 - len(errors))])
            client.indices.refresh(index=index)

        if failed:
            raise ValueError(
                f"{failed} documents were rejected by Elasticsearch ({indexed} indexed). "
                f"First errors: {'; '.join(errors)}"
            )
        return indexed

    def _value(self, name: str) -> Any:
        control = self.data.get(name)
        return control.get('value') if isinstance(control, dict) else None

    async def _retrieveParams(self) -> tuple[ElasticDataset, str, Literal['fail', 'replace', 'append'], Optional[str]]:
        """Retrieve the node configuration.

        Returns:
            tuple: dataset, index name, ifExist option and id field

        Raises:
            ValueError: If no data source or index is selected, or the index name is invalid.
        """
        dataset_id = self._value('selectDataSource')
        if not dataset_id:
            raise ValueError("No data source selected")
        dataset: ElasticDataset = await self.datasetService.get_dataset(dataset_id)
        if not isinstance(dataset, ElasticDataset):
            raise ValueError("The data source is not an Elasticsearch dataset")
        index = self._value('indexAutoComplete') or dataset.index
        if not index:
            raise ValueError("No index selected")
        _validate_es_index(index)
        if_exist = self._value('selectExist') or 'fail'
        if if_exist not in ('fail', 'replace', 'append'):
            raise ValueError(f"Invalid ifExist option: {if_exist}")
        id_field = self._value('idField') or None
        return dataset, index, if_exist, id_field

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
