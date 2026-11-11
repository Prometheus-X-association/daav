from typing import Annotated, Literal, TypeVar, Generic, Union, Optional
from bson import ObjectId
import numpy
from pandas import DataFrame
import pandas as pd
import pyarrow as pyarrow
from pyarrow.parquet import ParquetSchema
from pydantic import BaseModel, Field, WithJsonSchema, field_serializer
from app.models.interface.dataset_schema import MysqlSchema, PandasSchema

T = TypeVar('T')
D = TypeVar('D')

# Pydantic cannot describe these types in the OpenAPI schema: describe what their serializers return
JsonDataFrame = Annotated[DataFrame, WithJsonSchema({
    "type": "object",
    "additionalProperties": {"type": "object"},
    "description": "Data sample, by column then by row index (DataFrame.to_dict())",
})]
JsonParquetSchema = Annotated[ParquetSchema, WithJsonSchema({
    "type": "object",
    "properties": {"fields": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "physical_type": {"type": "string"},
            "logical_type": {"type": ["string", "null"]},
        },
    }}},
    "description": "Parquet columns",
})]

class NodeData(BaseModel, Generic[T, D]):
    model_config = {
        'arbitrary_types_allowed': True
    }
    dataExample: Optional[D] = None
    data: Optional[D] = None
    nodeSchema: T
    name: str
    type: Literal['mysql', 'mongo', 'elastic', 'file', 'api', 'pandasdf','parquet'] = None

    @field_serializer('data')
    def remove_data(cls, v):
        return None

class NodeDataMysql(NodeData[MysqlSchema, dict]):
    type: Literal['mysql'] = 'mysql'
    database: str
    table: str
    datasetId: str

class NodeDataJson(NodeData[dict, dict]):
    type: Literal['json'] = 'json' 

class NodeDataPandasDf(NodeData[PandasSchema, JsonDataFrame]):
    type: Literal['pandasdf'] = 'pandasdf'

    @field_serializer('dataExample')
    def serialize_data_example(self, data_example: DataFrame, _info):
        if data_example is None:
            return None
        
        # Convertir le DataFrame en dictionnaire
        data = data_example.to_dict()
        if data is None:
            return None
        
        # Process each column in the DataFrame dictionary
        for k, v in data.items():
            data[k] = self._convert_objectid(v)
        return data

    def _convert_objectid(self, value):
        """Recursively convert ObjectId and numpy types to JSON-serializable types"""
        if isinstance(value, ObjectId):
            return str(value)
        elif isinstance(value, numpy.ndarray):
            return value.tolist() if value is not None else None
        elif hasattr(value, 'dtype') and 'numpy' in str(type(value)):
            # Handle numpy scalars explicitly
            if numpy.issubdtype(value.dtype, numpy.integer):
                return int(value)
            elif numpy.issubdtype(value.dtype, numpy.floating):
                return float(value)
            elif numpy.issubdtype(value.dtype, numpy.bool_):
                return bool(value)
            elif numpy.issubdtype(value.dtype, numpy.str_):
                return str(value)
            else:
                # For other numpy types, convert to Python type
                return value.item() if hasattr(value, 'item') else value
        elif isinstance(value, dict):
            # Handle nested dictionaries
            return {k: self._convert_objectid(v) for k, v in value.items()}
        elif isinstance(value, list):
            # Handle lists
            return [self._convert_objectid(item) for item in value]
        else:
            # Return unchanged for other types
            return value

class NodeDataParquet(NodeData[JsonParquetSchema, str]):
    type: Literal['parquet'] = 'parquet'

    @field_serializer('dataExample')
    def serialize_data_example(self,data_example : str, _info):
        if data_example is not None:
            df = pd.read_parquet(data_example)
            return df.head(20).to_dict()
        elif self.data is not None:
            df = pd.read_parquet(self.data)
            return df.head(20).to_dict()
        return None
    
    @field_serializer('nodeSchema')
    def serialize_node_schema(self, node_schema : ParquetSchema, _info):
        if node_schema is not None:
            fields = []
            for field in node_schema:
                field_info = {
                    'name': field.name,
                    'physical_type': str(field.physical_type),
                    'logical_type': str(field.logical_type) if field.logical_type else None,
                }
                fields.append(field_info)
            
            return {
                'fields': fields,
            }
        return None

NodeDataUnion = Annotated[
    Union[NodeDataMysql, NodeDataPandasDf,NodeDataParquet],
    Field(discriminator='type')
]