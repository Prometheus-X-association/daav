from typing import Annotated, Any, ClassVar, Dict, List, Literal, Optional, Union
import re
import ipaddress
from urllib.parse import urlparse
from bson import ObjectId
from pydantic import BaseModel, Field, model_serializer, model_validator, ConfigDict, field_validator
from beanie import Document, PydanticObjectId, UnionDoc, before_event, after_event, Insert, Replace, Save
from datetime import datetime
from app.enums.type_connection import TypeConnection
from fastapi_pagination import LimitOffsetPage
from app.utils.encryption import encrypt_field, decrypt_field

# SQL identifiers: only letters, digits, underscore (max 64 chars - MySQL limit)
_SQL_IDENTIFIER_RE = re.compile(r'^[A-Za-z0-9_]{1,64}$')

# Elasticsearch index names: letters, digits, underscore, hyphen, dot
_ES_INDEX_RE = re.compile(r'^[a-z0-9_\-\.]{1,255}$')

# Private / local networks to block to prevent SSRF
_PRIVATE_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),  # link-local / AWS metadata
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
]

def _validate_sql_identifier(value: Optional[str], field_name: str) -> Optional[str]:
    if not value:
        return value
    if not _SQL_IDENTIFIER_RE.match(value):
        raise ValueError(
            f"'{field_name}' contains invalid characters. "
            "Only alphanumeric characters and underscores are allowed (max 64)."
        )
    return value

def _validate_no_ssrf(value: Optional[str], field_name: str) -> Optional[str]:
    if not value:
        return value
    try:
        parsed = urlparse(value)
    except Exception:
        raise ValueError(f"'{field_name}' is not a valid URL.")
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"'{field_name}' must use http or https scheme.")
    hostname = parsed.hostname or ''
    if hostname.lower() in ('localhost', '0.0.0.0', ''):
        raise ValueError(f"'{field_name}' must not point to localhost.")
    try:
        ip = ipaddress.ip_address(hostname)
        for network in _PRIVATE_NETWORKS:
            if ip in network:
                raise ValueError(
                    f"'{field_name}' must not point to a private or internal address."
                )
    except ValueError as exc:
        # Re-raise only SSRF-related errors; hostname strings (non-IP) are fine
        if 'private' in str(exc) or 'internal' in str(exc) or 'localhost' in str(exc):
            raise
    return value

class DatasetMetadata(BaseModel):
    fileSize: Optional[str] = None
    fileType: Optional[str] = None
    modifTime: Optional[str] = None
    accessTime: Optional[str] = None
    columnCount: Optional[str] = None
    rowCount: Optional[str] = None

class Dataset(Document):
    id: Optional[str] = Field(default=None, alias="_id")
    name: Optional[str] = None
    type: Literal['mysql','mongo','elastic','file','api', 'ptx'] = None
    metadata: Optional[DatasetMetadata] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # User ownership and sharing
    owner_id: Optional[str] = Field(default=None, description="ID of the user who owns this dataset")
    shared_with: List[str] = Field(default_factory=list, description="List of user IDs this dataset is shared with")

    # Subclasses declare their sensitive field names here
    _sensitive_fields: ClassVar[List[str]] = []

    @model_validator(mode='after')
    def decrypt_sensitive_fields(self) -> 'Dataset':
        """Decrypt sensitive fields after model instantiation (DB read or API input)."""
        for field in self.__class__._sensitive_fields:
            val = getattr(self, field, None)
            if val:
                object.__setattr__(self, field, decrypt_field(val))
        return self

    @before_event(Insert, Replace, Save)
    async def encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before writing to MongoDB."""
        for field in self.__class__._sensitive_fields:
            val = getattr(self, field, None)
            if val:
                object.__setattr__(self, field, encrypt_field(val))

    @after_event(Insert, Replace, Save)
    async def restore_sensitive_fields(self):
        """Decrypt sensitive fields back in-memory after the DB write."""
        for field in self.__class__._sensitive_fields:
            val = getattr(self, field, None)
            if val:
                object.__setattr__(self, field, decrypt_field(val))

    @before_event(Insert)
    async def generate_string_id(self):
        """Générer un ID string avant l'insertion"""
        if not self.id:
            self.id = str(ObjectId())
    
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True
    )
    
    class Settings:
        name = "datasets"
        is_root = True
        class_id = "type"
        use_state_management = True
        indexes = [
            [("type", 1)],
            [("name", 1)],
            [("created_at", -1)],
            [("owner_id", 1)]
        ]
    
    @model_serializer(mode='wrap')
    def serialize_model(self, serializer, info) -> Dict[str, Any]:
        data = serializer(self)
        if '_id' in data:
            data['id'] = str(data.pop('_id'))
        elif 'id' in data and data['id']:
            data['id'] = str(data['id'])

        # Remove all sensitive fields from API output
        for field in self._sensitive_fields:
            if field in data:
                data.pop(field)

        return data

class MysqlDataset(Dataset):
    type: Literal['mysql']


    class Settings:
        class_id = "type"
        class_id_value = "mysql"

    host: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    table: Optional[str] = None

    _sensitive_fields: ClassVar[List[str]] = ['password']

    @field_validator('database', mode='before')
    @classmethod
    def validate_database(cls, v):
        return _validate_sql_identifier(v, 'database')

    @field_validator('table', mode='before')
    @classmethod
    def validate_table(cls, v):
        return _validate_sql_identifier(v, 'table')
        

class MongoDataset(Dataset):
    type: Literal['mongo']

    class Settings:
        class_id = "type"
        class_id_value = "mongo"

    uri: Optional[str] = None
    database: Optional[str] = None
    collection: Optional[str] = None

    _sensitive_fields: ClassVar[List[str]] = ['uri']

class ElasticDataset(Dataset):
    type: Literal['elastic']

    class Settings:
        class_id = "type"
        class_id_value = "elastic"

    url: Optional[str] = None
    user: Optional[str] = None
    key: Optional[str] = None
    bearerToken: Optional[str] = None
    password: Optional[str] = None
    index: Optional[str] = None

    _sensitive_fields: ClassVar[List[str]] = ['password', 'key', 'bearerToken']

    @field_validator('url', mode='before')
    @classmethod
    def validate_url(cls, v):
        return _validate_no_ssrf(v, 'url')

    @field_validator('index', mode='before')
    @classmethod
    def validate_index(cls, v):
        if not v:
            return v
        if v in ('*', '_all', '.*'):
            raise ValueError("'index' must not be a wildcard expression.")
        if not _ES_INDEX_RE.match(v):
            raise ValueError(
                "'index' contains invalid characters. "
                "Only lowercase alphanumeric, underscore, hyphen, and dot are allowed (max 255)."
            )
        return v

class PTXDataset(Dataset):
    type: Literal['ptx']

    class Settings:
        class_id = "type"
        class_id_value = "ptx"

    url: Optional[str] = None
    token: Optional[str] = None
    refreshToken: Optional[str] = None
    service_key: Optional[str] = None
    secret_key: Optional[str] = None

    _sensitive_fields: ClassVar[List[str]] = ['token', 'refreshToken', 'secret_key', 'service_key']

class FileDataset(Dataset):
    type: Literal['file']

    class Settings:
        class_id = "type"
        class_id_value = "file"

    filePath: Optional[str] = None
    folder: Optional[str] = None
    inputType: Optional[str] = None
    csvHeader: Optional[str] = None
    csvDelimiter: Optional[str] = None
    ifExist: Optional[str] = None

class ApiDataset(Dataset):
    type: Literal['api']

    class Settings:
        class_id = "type"
        class_id_value = "api"

    apiAuth: Optional[str] = None
    url: Optional[str] = None
    authUrl: Optional[str] = None
    bearerToken: Optional[str] = None
    basicToken: Optional[str] = None
    clientId: Optional[str] = None
    clientSecret: Optional[str] = None

    _sensitive_fields: ClassVar[List[str]] = ['bearerToken', 'basicToken', 'clientSecret']

    @field_validator('url', mode='before')
    @classmethod
    def validate_url(cls, v):
        return _validate_no_ssrf(v, 'url')

    @field_validator('authUrl', mode='before')
    @classmethod
    def validate_auth_url(cls, v):
        return _validate_no_ssrf(v, 'authUrl')

DatasetUnion = Annotated[
    Union[MysqlDataset, MongoDataset, ElasticDataset, PTXDataset, FileDataset, ApiDataset],
    Field(discriminator='type')
]    

class Pagination(BaseModel):
    page: Optional[int] = None
    perPage: Optional[int] = None
    nextUrl: Optional[str] = None
    
class DatasetParams(BaseModel):
    database: Optional[str] = None
    table: Optional[str] = None

    @field_validator('database', mode='before')
    @classmethod
    def validate_database(cls, v):
        return _validate_sql_identifier(v, 'database')

    @field_validator('table', mode='before')
    @classmethod
    def validate_table(cls, v):
        return _validate_sql_identifier(v, 'table')

class ConnectionInfo(BaseModel):
    dataset: DatasetUnion
    pagination: Pagination
    datasetParams: DatasetParams 

class BasicContentResponse(BaseModel):
    # data: Optional[List[Dict[str, Any]]] = None
    data: Optional[list | Dict] = None
    total_rows: Optional[int] = None
    limit: Optional[int] = None
    current_page: Optional[int] = None

class MySQLContentResponse(BasicContentResponse):    
    databases: Optional[list] = None
    tables: Optional[list] = None
    table_description: Optional[List[Dict[str, Any]]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "databases": ["db1", "db2", "db3"],
                "tables": ["table1", "table2", "table3"],
                "table_description": [
                    {"Field": "id", "Type": "int(11)", "Null": "NO", "Key": "PRI", "Default": None, "Extra": "auto_increment"},
                    {"Field": "name", "Type": "varchar(255)", "Null": "YES", "Key": "", "Default": None, "Extra": ""}
                ],
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    }

class MongoContentResponse(BasicContentResponse):
    databases: Optional[list] = None
    collections: Optional[list] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "databases": ["db1", "db2", "db3"],
                "collections": ["collection1", "collection2", "collection3"],
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    }
    
class ElasticContentResponse(BasicContentResponse):
    indices: Optional[list | str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "indices": ["index1", "index2", "index3"],
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    }

class FileContentResponse(BasicContentResponse):
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    }

class ApiContentResponse(BasicContentResponse):
    next_url: Optional[str] = None
    prev_url: Optional[str] = None
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100,
                "next_url" : "https://api.example.com/items/?page=2"
            }
        }
    }

class PandaContentResponse(BasicContentResponse):
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    } 

DatasetContentResponse =  FileContentResponse | MongoContentResponse | MySQLContentResponse | ApiContentResponse | ElasticContentResponse