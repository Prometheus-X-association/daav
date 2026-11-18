from typing import List, Union, Optional
from pydantic import BaseModel, RootModel

class MysqlField(BaseModel):
    Field: str
    Type: str
    Null: str
    Key: str
    Default: Optional[str] = None
    Extra: str

class MysqlSchema(RootModel[List[MysqlField]]):
    pass

class PandasColumn(BaseModel):
    name: str
    dtype: str
    nullable: bool
    count: int
    nested: Optional[List["PandasColumn"]] = None

class PandasSchema(RootModel[List[PandasColumn]]):
    pass

DatasetSchema = Union[MysqlSchema, PandasSchema, dict]