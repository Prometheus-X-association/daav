import base64
import hmac
import json
import logging
import os
from typing import Dict, List, NoReturn, Optional, TYPE_CHECKING
from urllib.parse import urlparse

import duckdb
import pandas as pd
import numpy as np
from app.config.settings import settings
from app.models.interface.dataset_interface import Pagination, FileContentResponse
from app.models.interface.dataset_schema import PandasColumn, PandasSchema
from app.utils.security import PathSecurityValidator
from fastapi import HTTPException, Request, Header

if TYPE_CHECKING:
    from app.models.interface.user_interface import User

logger = logging.getLogger(__name__)

def get_user_output_path(node_id: str, user: Optional["User"] = None) -> str:
    """
    Get output file path with user isolation.
    
    Args:
        node_id (str): The node ID for the output file
        user (Optional[User]): The user object (optional, for user-specific directory)
        
    Returns:
        str: The complete file path with user directory if user provided
    """
    filename = f"{node_id}-output.json"
    
    if user:
        # Create user-specific directory: uploads/{user_id}/
        user_upload_dir = os.path.join(settings.upload_dir, user.id)
        os.makedirs(user_upload_dir, exist_ok=True)
        file_path = os.path.join(user_upload_dir, filename)
        logger.info(f"Using user directory for output: {user_upload_dir}")
        return file_path
    else:
        # Fallback to general uploads directory
        file_path = os.path.join(settings.upload_dir, filename)
        logger.info(f"Using general directory for output: {settings.upload_dir}")
        return file_path

# Schéma minimal JSON:API pour validation avec jsonschema
json_api_schema = {
    "type": "object",
    "properties": {
        "data": {"type": ["array", "object"]},
        "links": {
            "type": "object",
            "properties": {
                "self": {"type": "string"},
                "next": {"type": ["string", "null"]},
                "prev": {"type": ["string", "null"]}
            },
            "required": ["self"]
        },
        "meta": {"type": "object"}
    },
    "required": ["data", "links"]
}

custom_api_schema = {
    "type": "object",
    "properties": {
        "data": {"type": "array"},
        "count": {"type": "integer"},
        "self": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "href": {"type": "string"}
            },
            "required": ["href"]
        },
        "next": {
            "type": ["object", "null"],
            "properties": {
                "title": {"type": "string"},
                "href": {"type": "string"}
            },
            "required": ["href"]
        },
        "prev": {
            "type": ["object", "null"],
            "properties": {
                "title": {"type": "string"},
                "href": {"type": "string"}
            },
            "required": ["href"]
        }
    },
    "required": ["data", "count", "self"]
}

# Python type name of numpy scalars, checked in order
_NUMPY_SCALAR_TYPE_NAMES = (
    ((np.bool_, bool), "bool"),
    ((np.int8, np.int16, np.int32, np.int64), "int"),
    ((np.uint8, np.uint16, np.uint32, np.uint64), "int"),
    ((np.float16, np.float32, np.float64), "float"),
    ((np.complex64, np.complex128), "complex"),
    (np.str_, "str"),
    (np.bytes_, "bytes"),
)

# Python type name of a dtype, by substring of its name, checked in order
_DTYPE_NAME_PATTERNS = (
    (("int",), "int"),
    (("float",), "float"),
    (("bool",), "bool"),
    (("str", "object"), "str"),
)


def _dtype_name(dtype_str: str) -> Optional[str]:
    """Python type name of a numpy dtype string, or None if it is not recognized."""
    for patterns, name in _DTYPE_NAME_PATTERNS:
        if any(pattern in dtype_str for pattern in patterns):
            return name
    return None


def convert_numpy_type_to_python(value) -> str:
    """Convert numpy types to standard Python type names to avoid deprecation warnings."""
    for types, name in _NUMPY_SCALAR_TYPE_NAMES:
        if isinstance(value, types):
            return name
    # Handle some common numpy array dtypes
    if hasattr(value, 'dtype'):
        dtype_name = _dtype_name(str(value.dtype))
        if dtype_name:
            return dtype_name
    # For other types, use the standard type name
    return type(value).__name__


def normalize_dtype_string(dtype) -> str:
    """Normalize pandas/numpy dtype to avoid deprecated type warnings."""
    dtype_str = str(dtype)
    
    # Map deprecated numpy types to modern equivalents
    dtype_map = {
        'bool': 'bool',
        'int8': 'int',
        'int16': 'int', 
        'int32': 'int',
        'int64': 'int',
        'uint8': 'int',
        'uint16': 'int',
        'uint32': 'int', 
        'uint64': 'int',
        'float16': 'float',
        'float32': 'float',
        'float64': 'float',
        'complex64': 'complex',
        'complex128': 'complex',
        'object': 'str',
        'string': 'str',
        'datetime64': 'datetime',
        'timedelta64': 'timedelta'
    }
    
    # Check for exact matches or partial matches
    for np_type, python_type in dtype_map.items():
        if np_type in dtype_str.lower():
            return python_type
            
    return dtype_str


def convert_size(size: int) -> str:
    import math

    if size == 0:
        return "0B"
    size_units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return "%s %s" % (s, size_units[i])

# Extensions read as text by folder(), in addition to the text/* MIME types
_TEXT_EXTENSIONS = ['txt', 'log', 'md', 'py', 'js', 'html', 'css']
# Extensions read as base64 media by folder(), in addition to the image, audio and video MIME types
_MEDIA_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico',
                     'mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a', 'wma',
                     'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', '3gp']


def _read_json_file(path: str):
    with open(path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file)


def _read_csv_rows(path: str) -> list:
    import csv
    with open(path, 'r', encoding='utf-8') as csv_file:
        return list(csv.DictReader(csv_file))


def _read_yaml_file(path: str):
    import yaml
    with open(path, 'r', encoding='utf-8') as yaml_file:
        return yaml.safe_load(yaml_file)


def _read_text_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as text_file:
        return text_file.read()


# Content readers of folder(): (matches(mime, extension), reader, label), checked in order
_FOLDER_CONTENT_READERS = (
    (lambda mime, ext: mime == 'application/json' or ext == 'json', _read_json_file, "JSON file"),
    (lambda mime, ext: mime == 'text/csv' or ext == 'csv', _read_csv_rows, "CSV file"),
    (lambda mime, ext: mime == 'application/xml' or ext in ['xml', 'xsd'], _read_text_file, "XML file"),
    (lambda mime, ext: ext in ['yml', 'yaml'], _read_yaml_file, "YAML file"),
    (lambda mime, ext: mime.startswith('text/') or ext in _TEXT_EXTENSIONS, _read_text_file, "text file"),
)


def _is_media(mime: str, file_ext: str) -> bool:
    return mime.startswith(('image/', 'audio/', 'video/')) or file_ext in _MEDIA_EXTENSIONS


def _safe_read(reader, path: str, error_message: str):
    """Run the reader on the path; print the error and return None if it fails."""
    try:
        return reader(path)
    except Exception as e:
        print(f"{error_message}: {e}")
        return None


def _read_media_base64(path: str, name: str, file_size: int, max_size: int) -> Optional[str]:
    """Base64 content of a media file, or None if it is larger than max_size."""
    if file_size > max_size:
        print(f"Media file {name} too large ({convert_size(file_size)}) - 50 MB limit")
        return None
    with open(path, "rb") as media_file:
        return base64.b64encode(media_file.read()).decode('utf-8')


def _read_entry_content(entry: os.DirEntry, mime: str, file_ext: str, file_size: int, max_size: int) -> tuple:
    """Return (content, base64 media) of a file, according to its MIME type and extension."""
    for matches, reader, label in _FOLDER_CONTENT_READERS:
        if matches(mime, file_ext):
            return _safe_read(reader, entry.path, f"Error opening {label} {entry.name}"), None
    if _is_media(mime, file_ext):
        media = _safe_read(lambda path: _read_media_base64(path, entry.name, file_size, max_size), entry.path,
                           f"Error during base64 conversion of media file {entry.name}")
        return None, media
    return None, None


def _describe_file(entry: os.DirEntry, folder_path: str, max_size: int) -> dict:
    """Metadata and content of a file listed by folder()."""
    from datetime import datetime, timezone
    import magic

    stats = entry.stat()
    mime = magic.from_file(entry.path, mime=True)
    size = str(convert_size(stats.st_size))
    created = str(datetime.fromtimestamp(stats.st_ctime, tz=timezone.utc)).rsplit('.', 1)[0]
    modified = str(datetime.fromtimestamp(stats.st_mtime)).rsplit('.', 1)[0]
    file_ext = entry.name.lower().split('.')[-1] if '.' in entry.name else ''
    content, base_64 = _read_entry_content(entry, mime, file_ext, stats.st_size, max_size)
    return {
        'media': base_64,
        'path': entry.path,
        'folder': folder_path,
        'file': entry.name,
        'mime_type': mime,
        'size': size,
        'created': created,
        'modified': modified,
        'content': content
    }


def _iter_files(folder_path: str):
    """Yield (entry, folder path) for each file of the folder, depth first; access errors are printed and skipped."""
    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                yield from _iter_entry(entry, folder_path)
    except OSError as e:
        print(f"Access error to folder {folder_path}: {e}")


def _iter_entry(entry: os.DirEntry, folder_path: str):
    try:
        if entry.is_dir():
            yield from _iter_files(entry.path)
        elif entry.is_file():
            yield entry, folder_path
    except OSError as e:
        print(f"Access error to {entry.path}: {e}")


# Folder reading function
def folder(folder: str, pagination: Pagination = None) -> FileContentResponse | list:
    # SECURITY: Input path validation (uses centralized security bypass)
    from app.utils.security import PathSecurityValidator, FileAccessController
    from app.config.security import SecurityConfig

    # Use centralized security validation (automatically handles test environment bypass)
    validated_folder = PathSecurityValidator.validate_file_path(folder)
    # Get allowed directories list (including dynamic upload_dir)
    allowed_base_dirs = SecurityConfig.get_allowed_base_directories()
    if not FileAccessController.can_read_file(validated_folder, allowed_base_dirs):
        raise PermissionError(f"Access denied to directory: {folder}")

    donnees = []
    max_size = settings.max_file_size  # Get max file size from settings
    file_count = 0  # Total file counter

    # calculate pagination indices
    if pagination:
        start_index = (pagination.page - 1) * pagination.perPage
        end_index = start_index + pagination.perPage
    else:
        start_index = 0
        end_index = float('inf')  # No limit

    # Use the folder (already security validated)
    for entry, folder_path in _iter_files(validated_folder):
        # Count every file, but only describe the files of the requested page
        current_file_index = file_count
        file_count += 1
        if start_index <= current_file_index < end_index:
            try:
                donnees.append(_describe_file(entry, folder_path, max_size))
            except OSError as e:
                print(f"Access error to {entry.path}: {e}")

    # Return according to requested format
    if pagination is None:
        return donnees
    return FileContentResponse(
        data=donnees,
        total_rows=file_count,
        current_page=pagination.page,
        limit=pagination.perPage
    )


def generate_pandas_schema(data: pd.DataFrame | pd.Series | dict) -> PandasSchema:
    if isinstance(data, pd.DataFrame):
        schema = _schema_from_dataframe(data)
    elif isinstance(data, pd.Series):
        schema = _schema_from_series(data)
    elif isinstance(data, dict):
        schema = _schema_from_dict(data)
    else:
        schema = []
    return PandasSchema(root=schema)


# Column name of the items of a collection without name: the parent collection takes their type
_ARRAY_ITEM_TAG = "#array_item#"


def _schema_from_dataframe(data: pd.DataFrame) -> List[PandasColumn]:
    return [_dataframe_column(data, column) for column in data.columns]


def _dataframe_column(data: pd.DataFrame, column) -> PandasColumn:
    values = data[column]
    col_schema = PandasColumn(
        name=str(column),
        dtype=normalize_dtype_string(values.dtype),
        nullable=values.isnull().any(),
        count=values.notnull().sum(),
        nested=None
    )
    if isinstance(values, (pd.Series, pd.DataFrame, dict)):
        nested_schema = generate_pandas_schema(values)
        col_schema.nested = nested_schema.root
        # An empty column has no item to take the type from: keep the column dtype
        if nested_schema.root and isinstance(values, pd.Series) and isinstance(values.index, pd.RangeIndex) and data.index.start == 0:
            col_schema.dtype = nested_schema.root[0].dtype
            col_schema.count = values.size
            if nested_schema.root[0].name == _ARRAY_ITEM_TAG:
                col_schema.nested = None
    return col_schema


def _schema_from_series(data: pd.Series) -> List[PandasColumn]:
    if len(data) == 0:
        return []
    non_null_values = data.dropna()
    if len(non_null_values) == 0:
        # Series without values
        return [PandasColumn(
            name=_ARRAY_ITEM_TAG,
            dtype=normalize_dtype_string(data.dtype),
            nullable=True,
            count=0,
            nested=None
        )]
    sample_value = non_null_values.iloc[0]
    if isinstance(sample_value, (dict, list, pd.Series, pd.DataFrame)):
        # Series of dictionaries or of more complex structures
        return _schema_from_series_items(data)
    # Series of simple types
    return [PandasColumn(
        name=_ARRAY_ITEM_TAG,
        dtype=convert_numpy_type_to_python(sample_value),
        nullable=data.isnull().any(),
        count=data.size,
        nested=None
    )]


def _schema_from_series_items(data: pd.Series) -> List[PandasColumn]:
    schema: List[PandasColumn] = []
    for idx in data.index:
        col_schema, nested_schema = _series_item_column(idx, data.get(idx), schema)
        schema.append(col_schema)
        # If it's an array-like Series, stop after the first item and return the inner nested object of the first row
        if isinstance(data.index, pd.RangeIndex) and data.index.start == 0 and nested_schema and len(nested_schema.root) > 0:
            return nested_schema.root
    return schema


def _series_item_column(idx, value, schema: List[PandasColumn]) -> tuple:
    """Return (column, nested schema or None) of an item of a Series of structures."""
    item_name = str(idx)
    if not isinstance(value, list) and pd.isna(value):
        return PandasColumn(name=item_name, dtype="NaN", nullable=True, count=0, nested=None), None

    col_schema = PandasColumn(
        name=item_name,
        dtype=convert_numpy_type_to_python(value),
        nullable=False,
        count=1,
        nested=None
    )
    nested_schema = _nested_schema(value)
    if nested_schema is not None:
        col_schema.nested = nested_schema.root
    elif isinstance(value, list) and len(value) > 0:
        # list with simple type: replace the schema with only one item
        nested_schema = PandasSchema(root=schema)
        col_schema = PandasColumn(
            name="#value",
            dtype=f"Array[{convert_numpy_type_to_python(value[0])}]",
            nullable=False,
            count=1,
            nested=None
        )
        nested_schema.root.append(col_schema)
    return col_schema, nested_schema


def _schema_from_dict(data: dict) -> List[PandasColumn]:
    schema: List[PandasColumn] = []
    for key, value in data.items():
        col_schema = PandasColumn(
            name=str(key),
            dtype=convert_numpy_type_to_python(value),
            nullable=value is None,
            count=0 if value is None else 1,
            nested=None
        )
        # Recursive handling of nested structures
        nested_schema = _nested_schema(value)
        if nested_schema is not None:
            col_schema.nested = nested_schema.root
        schema.append(col_schema)
    return schema


def _nested_schema(value) -> Optional[PandasSchema]:
    """Schema of a nested structure, or of the first object of a list of objects; None for other values."""
    if isinstance(value, (pd.Series, pd.DataFrame, dict)):
        return generate_pandas_schema(value)
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return generate_pandas_schema(value[0])
    return None


def slice_generator(df, chunk_size=1000):
    current_row = 0
    total_rows = df.shape[0]
    while current_row < total_rows:
        yield df[current_row:current_row + chunk_size]
        current_row += chunk_size


def decode_dictionary(dictionary):
    if isinstance(dictionary, dict):
        for key in dictionary.keys():
            dictionary[key] = decode_dictionary(dictionary[key])
    elif isinstance(dictionary, bytes):
        dictionary = dictionary.decode('ISO-8859-1') 
    return dictionary

def resolve_file_name(filename: str, expected_ext: str) -> str:
        """
        Ensures the filename ends with the correct extension.
        - Adds the extension if it's missing.
        - Replaces the extension if it's different from the expected one.
        - Returns the filename as-is if the extension matches.
        
        Args:
            filename (str): The original file name.
            expected_ext (str): The desired extension (without dot), e.g. 'csv', 'json'.
        
        Returns:
            str: The corrected filename with the expected extension.
            
        Raises:
            ValueError: If the file extension is not allowed by security validator.
        """
        expected_ext = expected_ext.lower()
        base, ext = os.path.splitext(filename)
        ext = ext.lstrip(".").lower()
        
        # Determine the final filename
        if not ext:
            final_filename = f"{filename}.{expected_ext}"
        elif ext != expected_ext:
            final_filename = f"{base}.{expected_ext}"
        else:
            final_filename = filename
        
        # Validate the final filename for security
        if not PathSecurityValidator.validate_file_extension(final_filename):
            raise ValueError(f"File extension '{expected_ext}' is not allowed for security reasons")
        
        return final_filename

def filter_data_with_duckdb(filepath: str, select: Optional[str] = None, where: Optional[str] = None, params: Optional[str] = None) -> list | dict:
    """
    Filter JSON data using DuckDB with optional SELECT and WHERE clauses
    
    Args:
        filepath: path to the JSON file
        select: Columns to select (comma separated)
        where: WHERE clause conditions
    
    Returns:
        Filtered data as list of dictionaries
    """
    try:
        # Read and return the output file
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not (select or where):
            return data
            
        # Convert JSON data to DuckDB table
        # Convert JSON data to DuckDB table
        con = duckdb.connect(":memory:")
        
        con.execute("CREATE TABLE temp_data AS SELECT * FROM read_json(?)", [filepath])

        # The WHERE clause is built from the query string: once the data is loaded,
        # forbid any file or network access (and re-enabling it) from the query
        con.execute("SET enable_external_access = false")
        con.execute("SET lock_configuration = true")

        # Construct SQL query
        query = "SELECT "
        query += select if select else "*"
        query += " FROM temp_data"
        if where:
            query += f" WHERE {where}"
        
        # Execute query and fetch results
        result = con.execute(query, params).fetchall()
        column_names = con.execute("SELECT * FROM temp_data LIMIT 0").description
        
        # Convert results to dict format
        filtered_data = [
            {column_names[i][0]: value for i, value in enumerate(row)}
            for row in result
        ]

        # Close the connection
        con.close()
        return filtered_data
        
    except Exception as e:
        logger.exception(f"Error filtering data with DuckDB: {e}")
        raise HTTPException(status_code=500, detail=f"Error filtering data: {str(e)}")


def _secret_equals(value: str, expected: str) -> bool:
    """Compare a received credential with the expected one in constant time"""
    return hmac.compare_digest(str(value).encode(), str(expected).encode())


def verify_route_access(
    request: Request,
    api_keys: Optional[List[str | Dict[str, str]]] = None
) -> None:
    """
    Verify route access using domain whitelist or API keys.
    
    Checks in order:
    1. Domain whitelist (from env DOMAIN_WHITELIST)
    2. API keys (mixed list of Bearer tokens and custom headers)
    
    Args:
        request: FastAPI Request object
        api_keys: List of mixed items:
            - str: Bearer token (e.g., "token123")
            - dict: Custom header (e.g., {"X-API-Key": "value"})
        
    Returns when access is granted.

    Raises:
        HTTPException: 403 if access denied
        
    Examples:
        verify_route_access(request)  # Whitelist only
        verify_route_access(request, api_keys=["token1", "token2"])  # Bearer tokens
        verify_route_access(request, api_keys=[{"X-Key": "val"}])  # Custom headers
        verify_route_access(request, api_keys=["token1", {"X-Key": "val"}])  # Mixed
    """

    if _origin_is_whitelisted(request):
        return

    # Deny if no api_keys provided
    if not api_keys:
        _deny(request)

    # Get authorization header from request
    authorization = request.headers.get("authorization")
    if any(_matches_api_key(request, api_key, authorization) for api_key in api_keys):
        return

    _deny(request)


def _origin_is_whitelisted(request: Request) -> bool:
    """True if the Origin (or Referer) header is a domain of the whitelist (from env DOMAIN_WHITELIST) or one of its subdomains."""
    if not settings.domain_whitelist:
        return False
    origin = request.headers.get("origin") or request.headers.get("referer")
    if not origin:
        return False
    parsed = urlparse(origin)
    domain = parsed.netloc or parsed.path.split('/')[0]
    for whitelisted_domain in settings.domain_whitelist:
        if domain == whitelisted_domain or domain.endswith(f".{whitelisted_domain}"):
            logger.info(f"Route access granted via domain whitelist: {domain}")
            return True
    return False


def _matches_api_key(request: Request, api_key: str | Dict[str, str], authorization: Optional[str]) -> bool:
    """True if the request carries the API key: a Bearer token (str) or custom headers (dict)."""
    if isinstance(api_key, str):
        return _matches_bearer_token(authorization, api_key)
    if isinstance(api_key, dict):
        return _matches_custom_headers(request, api_key)
    return False


def _matches_bearer_token(authorization: Optional[str], api_key: str) -> bool:
    if not (authorization and authorization.startswith("Bearer ")):
        return False
    token = authorization.replace("Bearer ", "").strip()
    if _secret_equals(token, api_key):
        logger.info("Route access granted via Bearer token")
        return True
    return False


def _matches_custom_headers(request: Request, api_key: Dict[str, str]) -> bool:
    # request.headers is case-insensitive
    for header_name, expected_value in api_key.items():
        value = request.headers.get(header_name)
        if value is not None and _secret_equals(value, expected_value):
            logger.info(f"Route access granted via custom header: {header_name}")
            return True
    return False


def _deny(request: Request) -> NoReturn:
    """Log and refuse the route access (403)."""
    logger.warning(f"Route access denied for request from {request.client.host if request.client else 'unknown'}")
    raise HTTPException(
        status_code=403,
        detail="Access denied. Valid authentication required."
    )
