import asyncio
import traceback
from typing import Any, List, Optional

from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import ElasticDataset, _validate_es_index
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.inputs.input_node import InputNode
from app.services.dataset_service import DatasetService
from app.services.elastic_service import ElasticService
from app.utils.utils import generate_pandas_schema

SAMPLE_SIZE = 20


class DataElasticBlock(InputNode):

    datasetService: Optional[DatasetService] = None
    elasticService: Optional[ElasticService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new DataElasticBlock instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)
        self.datasetService = DatasetService()
        self.elasticService = ElasticService()

    async def process(self, sample: bool = False) -> StatusNode:
        """Read the documents of an Elasticsearch index.

        Args:
            sample (bool): If True, retrieve only the first documents (default is False).

        Returns:
            StatusNode: The status of the node after processing.
        """
        try:
            dataset, index, query, fields, max_docs, include_id = await self._retrieveParams()
            if sample:
                size = min(SAMPLE_SIZE, max_docs) if max_docs else SAMPLE_SIZE
                df = await asyncio.to_thread(
                    self.elasticService.sample_dataframe, dataset, index, size, query, fields, include_id
                )
            else:
                df = await asyncio.to_thread(
                    self.elasticService.read_dataframe, dataset, index, query, fields, max_docs, include_id
                )
            schema = generate_pandas_schema(df)

            for key, output in self.outputs.items():
                if output.get_node_data():
                    output.get_node_data().nodeSchema = schema
                    if sample:
                        output.get_node_data().dataExample = df
                    else:
                        output.get_node_data().data = df
                else:
                    node_data = NodeDataPandasDf(nodeSchema=schema, name=index)
                    if sample:
                        node_data.dataExample = df
                    else:
                        node_data.data = df
                    output.set_node_data(node_data, self)
            return StatusNode.Valid
        except Exception as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error

    def _value(self, name: str) -> Any:
        control = self.data.get(name)
        return control.get('value') if isinstance(control, dict) else None

    async def _retrieveParams(self) -> tuple[ElasticDataset, str, Optional[str], Optional[List[str]], Optional[int], bool]:
        """Retrieve the node configuration.

        Returns:
            tuple: dataset, index, query, fields, maximum number of documents, include _id

        Raises:
            ValueError: If no data source or index is selected, or a parameter is invalid.
        """
        datasetId = self._value('selectDataSource')
        if not datasetId:
            raise ValueError("No data source selected")
        dataset: ElasticDataset = await self.datasetService.get_dataset(datasetId)
        if not isinstance(dataset, ElasticDataset):
            raise ValueError("The data source is not an Elasticsearch dataset")

        index = dataset.index or self._value('selectIndexDataSource')
        if not index:
            raise ValueError("No index selected")
        _validate_es_index(index)

        query = self._value('query') or None

        fields_value = self._value('fields')
        fields = [f.strip() for f in fields_value.split(',') if f.strip()] if fields_value else None

        max_docs = self._value('maxDocs')
        if max_docs in (None, ''):
            max_docs = None
        else:
            try:
                max_docs = int(max_docs)
            except (TypeError, ValueError):
                raise ValueError("The maximum number of documents must be a number")
            if max_docs <= 0:
                raise ValueError("The maximum number of documents must be positive")

        include_id = self._value('includeId')
        return dataset, index, query, fields, max_docs, include_id is not False

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
