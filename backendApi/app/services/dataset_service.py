# dataset_service.py

from contextvars import ContextVar
import os
import json
from fastapi import HTTPException, status
import shutil
import requests
import pandas as pd
import mysql.connector
from fastavro import reader
from bson import ObjectId
from datetime import datetime, timezone
from sqlalchemy import create_engine
from typing import List, Optional, Union, Dict, Any
import logging

from app.enums.type_connection import TypeConnection
from app.models.interface.dataset_interface import (
    DatasetUnion, Dataset, FileDataset, MongoDataset, MysqlDataset,
    ApiDataset, ElasticDataset, PTXDataset, DatasetParams, Pagination
)
from app.services.user_service import UserService
from app.models.interface.user_interface import User
from app.enums.user_role import UserRole
from app.utils.singleton import SingletonMeta
from app.models.interface.node_data import NodeDataPandasDf
from app.utils.utils import convert_size, folder, generate_pandas_schema
from app.utils.security import PathSecurityValidator, FileAccessController
from app.models.interface.pdc_chain_interface import PdcChainRequestData, PdcChainHeaders
from app.config.security import SecurityConfig

logger = logging.getLogger(__name__)

# Context variable to ensure isolation of PDC chain data
pdc_chain_data_var: ContextVar[Optional[dict]] = ContextVar('pdc_chain_data', default=None)
pdc_chain_headers_var: ContextVar[Optional[PdcChainHeaders]] = ContextVar('pdc_chain_headers', default=None)




class DatasetService(metaclass=SingletonMeta):
    
    def __init__(self):
        # Keep compatibility for migration
        self.config = {"connections": []}
        self.pdcChainData: Union[PdcChainRequestData, str, List[Any], Dict[str, Any]] = None
        self.pdcChainHeaders: PdcChainHeaders = None
        self.user_service = UserService()
        logger.info("DatasetService initialized")

    @property
    def pdcChainData(self):
        return pdc_chain_data_var.get()
    
    @pdcChainData.setter
    def pdcChainData(self, value):
        pdc_chain_data_var.set(value)
    
    @property
    def pdcChainHeaders(self):
        return pdc_chain_headers_var.get()
    
    @pdcChainHeaders.setter
    def pdcChainHeaders(self, value):
        pdc_chain_headers_var.set(value)

    async def get_datasets(self, user: Optional[User] = None) -> List[Dataset]:
        """
        Retrieve datasets with optional permission filtering.
        
        Args:
            user: User requesting access. If None, returns all datasets (for M2M calls)
            
        Returns:
            List of Dataset objects
            
        Raises:
            HTTPException: 500 on error
        """
        try:
            if user:
                logger.info(f"Getting datasets for user: {user.username}")

                # Admin can see all datasets
                if user.role == UserRole.ADMIN:
                    datasets = await Dataset.find(with_children=True).to_list()
                    logger.info(f"Admin retrieved {len(datasets)} datasets")
                    return datasets
                
                # Regular user - filter by owned + shared
                dataset_ids = user.owned_datasets + user.shared_datasets
                if not dataset_ids:
                    logger.info(f"User {user.username} has no datasets")
                    return []
                
                datasets = await Dataset.find({"_id": {"$in": dataset_ids}}, with_children=True).to_list()
                logger.info(f"User {user.username} retrieved {len(datasets)} datasets")
                return datasets
            else:
                # System call - return all datasets
                logger.info("System getting all datasets (no permission filtering)")
                datasets = await Dataset.find(with_children=True).to_list()
                return datasets
            
        except Exception as e:
            logger.error(f"Error in get_datasets: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_dataset(self, id: str, user: Optional[User] = None) -> Dataset:
        """
        Retrieve a single dataset by ID with optional permission check.
        
        Args:
            id: Dataset ID to retrieve
            user: User requesting access. If None, permission check is skipped (for M2M calls)
            
        Returns:
            Dataset object
            
        Raises:
            HTTPException: 404 if not found, 403 if access denied, 500 on error
        """
        try:
            if user:
                logger.info(f"User {user.username} fetching dataset with ID: {id}")
            else:
                logger.info(f"System fetching dataset with ID: {id} (no permission check)")
            
            # Get dataset
            dataset = await Dataset.get(id, with_children=True)
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found")

            # Only check permissions if user is provided
            if user:
                can_access = await self.user_service.can_access_dataset(user, id)
                if not can_access:
                    logger.warning(f"User {user.username} denied access to dataset {id}")
                    raise HTTPException(status_code=403, detail="Access denied")
                logger.info(f"User {user.username} successfully accessed dataset: {dataset.name}")
            else:
                logger.info(f"System successfully accessed dataset: {dataset.name}")
            
            return dataset
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving dataset {id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_dataset(self, id: str, user: User) -> bool:
        """Delete a dataset with permission check"""
        try:
            logger.info(f"User {user.username} attempting to delete dataset with ID: {id}")
            
            # Check permission using user_service
            can_modify = await self.user_service.can_modify_dataset(user, id)
            if not can_modify:
                logger.warning(f"User {user.username} denied permission to delete dataset {id}")
                raise HTTPException(status_code=403, detail="Access denied")
            
            dataset = await Dataset.get(id, with_children=True)
            if not dataset:
                logger.warning(f"Attempted to delete non-existent dataset: {id}")
                return False
            
            dataset_name = dataset.name
            dataset_type = dataset.type
            
            # Remove ownership relations BEFORE deleting
            await self.user_service.remove_dataset_ownership(id)
            
            # Type-specific cleanup
            if dataset_type == "file":
                logger.debug(f"Cleaning up files for dataset: {dataset_name}")
                self._cleanup_file_dataset(dataset)
            
            await dataset.delete()
            logger.info(f"User {user.username} successfully deleted dataset: {dataset_name} (Type: {dataset_type}, ID: {id})")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting dataset {id}: {e}", exc_info=True)
            return False

    def _cleanup_file_dataset(self, dataset: FileDataset):
        """Clean up files from a file dataset"""
        try:
            # SECURITY: Validate paths before deletion
            if dataset.folder:
                try:
                    validated_folder = PathSecurityValidator.validate_file_path(dataset.folder)                    
                    allowed_dirs = SecurityConfig.get_allowed_base_directories()
                    if not FileAccessController.can_read_file(validated_folder, allowed_dirs):
                        logger.error(f"Access denied for cleanup of folder: {dataset.folder}")
                        return
                    
                    if os.path.exists(validated_folder):
                        logger.debug(f"Removing folder: {validated_folder}")
                        shutil.rmtree(validated_folder)
                        logger.info(f"Successfully removed folder: {validated_folder}")
                except Exception as e:
                    logger.error(f"Security validation failed for folder cleanup {dataset.folder}: {e}")
                    return
                    
            elif dataset.filePath:
                try:
                    validated_file = PathSecurityValidator.validate_file_path(dataset.filePath)
                    allowed_dirs = SecurityConfig.get_allowed_base_directories()
                    if not FileAccessController.can_read_file(validated_file, allowed_dirs):
                        logger.error(f"Access denied for cleanup of file: {dataset.filePath}")
                        return
                    
                    if os.path.exists(validated_file):
                        logger.debug(f"Removing file: {validated_file}")
                        os.remove(validated_file)
                        logger.info(f"Successfully removed file: {validated_file}")
                except Exception as e:
                    logger.error(f"Security validation failed for file cleanup {dataset.filePath}: {e}")
                    return
        except Exception as e:
            logger.error(f"Error cleaning up files for dataset {dataset.name}: {e}", exc_info=True)

    async def add_connection(self, connection: DatasetUnion, user: User) -> dict:
        """Add a new connection with ownership assignment"""
        try:
            logger.info(f"User {user.username} adding new connection: {connection.name} (Type: {connection.type})")
            
            # Check for duplicates for this specific user
            if await self._connection_exists(connection, user):
                logger.warning(f"Connection already exists for user {user.username}: {connection.name} (Type: {connection.type})")
                return {"status": "Dataset already exists"}
            
            # Type-specific processing
            if isinstance(connection, FileDataset):
                logger.debug(f"Processing file dataset: {connection.name}")
                connection = self._process_file_dataset(connection)
            elif isinstance(connection, PTXDataset):
                logger.debug(f"Processing PTX dataset: {connection.name}")
                connection = self._process_ptx_dataset(connection)
            
            # Save dataset first
            await connection.insert()
            
            # Assign ownership (bidirectional)
            await self.user_service.assign_dataset_ownership(user, connection)
            
            logger.info(f"User {user.username} successfully added connection: {connection.name} (Type: {connection.type})")
            return {"status": "Connection added"}
            
        except Exception as e:
            logger.error(f"Error adding connection {connection.name}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to add connection")

    async def _connection_exists(self, connection: DatasetUnion, user: User) -> bool:
        """Check if a connection already exists for a specific user via their owned datasets"""
        
        # First, get all datasets owned by this user
        user_dataset_ids = user.owned_datasets
        
        if not user_dataset_ids:
            return False
        
        # Then check if the specific connection exists among user's datasets
        if isinstance(connection, FileDataset):
            if connection.filePath:
                existing = await FileDataset.find_one(
                    FileDataset.filePath == connection.filePath,
                    {"_id": {"$in": user_dataset_ids}}
                )
            elif connection.folder:
                existing = await FileDataset.find_one(
                    FileDataset.folder == connection.folder,
                    {"_id": {"$in": user_dataset_ids}}
                )
            else:
                existing = None
                
        elif isinstance(connection, MongoDataset):
            existing = await MongoDataset.find_one(
                MongoDataset.uri == connection.uri,
                MongoDataset.database == connection.database,
                MongoDataset.collection == connection.collection,
                {"_id": {"$in": user_dataset_ids}}
            )
            
        elif isinstance(connection, MysqlDataset):
            existing = await MysqlDataset.find_one(
                MysqlDataset.host == connection.host,
                MysqlDataset.database == connection.database,
                MysqlDataset.table == connection.table,
                MysqlDataset.user == connection.user,
                {"_id": {"$in": user_dataset_ids}}
            )
            
        elif isinstance(connection, ApiDataset):
            existing = await ApiDataset.find_one(
                ApiDataset.url == connection.url,
                {"_id": {"$in": user_dataset_ids}}
            )
            
        elif isinstance(connection, ElasticDataset):
            existing = await ElasticDataset.find_one(
                ElasticDataset.url == connection.url,
                ElasticDataset.index == connection.index,
                {"_id": {"$in": user_dataset_ids}}
            )
            
        elif isinstance(connection, PTXDataset):
            existing = await PTXDataset.find_one(
                PTXDataset.url == connection.url,
                {"_id": {"$in": user_dataset_ids}}
            )
            
        else:
            existing = None
            
        return existing is not None

    def _process_file_dataset(self, connection: FileDataset) -> FileDataset:
        """Process a file dataset to extract metadata"""
        try:
            if connection.filePath:
                # SECURITY: Validate file path before processing
                try:
                    validated_path = PathSecurityValidator.validate_file_path(connection.filePath)
                    allowed_dirs = SecurityConfig.get_allowed_base_directories()
                    if not FileAccessController.can_read_file(validated_path, allowed_dirs):
                        logger.error(f"Access denied to file path: {connection.filePath}")
                        raise HTTPException(status_code=403, detail="Access denied to file path")
                    connection.filePath = validated_path
                except Exception as e:
                    logger.error(f"Security validation failed for file path {connection.filePath}: {e}")
                    raise HTTPException(status_code=403, detail="Invalid or dangerous file path")
                
                if os.path.exists(connection.filePath):
                    logger.debug(f"Processing file metadata for: {connection.filePath}")
                    stats = os.stat(connection.filePath)
                file_size = stats.st_size
                
                logger.debug(f"File size: {file_size} bytes for {connection.filePath}")
                
                # Calculate column and row count by file type
                column_count = "0"
                row_count = "0"
                
                try:
                    if connection.filePath.endswith('.csv'):
                        df = pd.read_csv(connection.filePath, 
                                       header=int(connection.csvHeader), 
                                       delimiter=connection.csvDelimiter or ',')
                        column_count = str(len(df.columns))
                        row_count = str(len(df))
                    elif connection.filePath.endswith('.json'):
                        df = pd.read_json(connection.filePath)
                        column_count = str(df.shape[1])
                        row_count = str(df.shape[0])
                    elif connection.filePath.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(connection.filePath)
                        column_count = str(df.shape[1])
                        row_count = str(df.shape[0])
                    elif connection.filePath.endswith('.parquet'):
                        df = pd.read_parquet(connection.filePath)
                        column_count = str(df.shape[1])
                        row_count = str(df.shape[0])
                    # Add more file types as needed
                            
                except Exception as e:
                    logger.warning(f"Error processing file metadata: {e}")
                
                from app.models.interface.dataset_interface import DatasetMetadata
                connection.metadata = DatasetMetadata(
                    fileSize=str(convert_size(stats.st_size)),
                    fileType=connection.filePath.rsplit('.', 1)[1] if '.' in connection.filePath else 'unknown',
                    modifTime=str(datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc)).rsplit('.', 1)[0],
                    accessTime=str(datetime.fromtimestamp(stats.st_atime, tz=timezone.utc)).rsplit('.', 1)[0],
                    columnCount=column_count,
                    rowCount=row_count
                )
                
                logger.info(f"Successfully processed file dataset metadata for: {connection.filePath}")
            else:
                logger.warning(f"File not found or path not specified for dataset: {connection.name}")
                
        except Exception as e:
            logger.error(f"Error processing file dataset {connection.name}: {e}", exc_info=True)
        
        return connection

    def _process_ptx_dataset(self, connection: PTXDataset) -> PTXDataset:
        """Process a PTX dataset to get tokens"""
        if connection.url and connection.url.endswith("/"):
            connection.url = connection.url[:-1]
        
        # Get keys for authentication
        if connection.service_key and connection.secret_key:
            try:
                jwt = self.connect_pdc(connection.url, connection.service_key, connection.secret_key)
                connection.token = jwt["content"]["token"]
                connection.refreshToken = jwt["content"]["refreshToken"]
                # Clean sensitive keys after use
                connection.service_key = None
                connection.secret_key = None
            except Exception as e:
                logger.error(f"Error connecting to PDC: {e}")
        
        return connection

    def connect_pdc(self, url, service_key, secret_key):
        """Connect to PDC and return JWT"""
        try:
            logger.info(f"Connecting to PDC at: {url}")
            r = requests.post(url + "/login", {
                "secretKey": secret_key,
                "serviceKey": service_key
            })
            
            logger.debug(f"PDC response status: {r.status_code}")
            
            if r.status_code == 200:
                logger.info("Successfully authenticated with PDC")
            else:
                logger.warning(f"PDC authentication returned status: {r.status_code}")
            
            if 'json' in r.headers['Content-Type']:
                res = r.json()
            else:
                res = r.content
                
            return res
        except requests.RequestException as e:
            logger.error(f"Network error connecting to PDC {url}: {e}", exc_info=True)
            raise Exception(f"Failed to connect to PDC: {e}")
        except Exception as e:
            logger.error(f"Error connecting to PDC {url}: {e}", exc_info=True)
            raise Exception(e)

    async def edit_dataset(self, dataset: DatasetUnion, user: User) -> bool:
        """Edit an existing dataset with permission check"""
        try:
            logger.info(f"User {user.username} editing dataset: {dataset.id}")
            
            # Check permission using user_service
            can_modify = await self.user_service.can_modify_dataset(user, dataset.id)
            if not can_modify:
                logger.warning(f"User {user.username} denied permission to edit dataset {dataset.id}")
                raise HTTPException(status_code=403, detail="Access denied")
            
            existing = await Dataset.get(dataset.id, with_children=True)
            if not existing:
                raise HTTPException(status_code=404, detail="Dataset not found")

            # Restore missing sensitive fields from the persisted document.
            for field_name in getattr(existing, '_sensitive_fields', []):
                if getattr(dataset, field_name, None) is None and getattr(existing, field_name, None) is not None:
                    setattr(dataset, field_name, getattr(existing, field_name))

            if isinstance(dataset, PTXDataset):
                if dataset.service_key and dataset.secret_key:
                    dataset = self._process_ptx_dataset(dataset)

            dataset.updated_at = datetime.now(timezone.utc)
            await dataset.replace()
            logger.info(f"User {user.username} successfully edited dataset: {dataset.id}")
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error editing dataset: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to edit dataset")
    
    async def find_file_connection(self, folder: str, name: str = None) -> FileDataset:
        """Find an existing file connection or create it"""
        
        # SECURITY: Validate folder path before processing
        if folder:
            try:
                validated_folder = PathSecurityValidator.validate_file_path(folder)
                allowed_dirs = SecurityConfig.get_allowed_base_directories()
                if not FileAccessController.can_read_file(validated_folder, allowed_dirs):
                    logger.error(f"Access denied to folder: {folder}")
                    raise HTTPException(status_code=403, detail="Access denied to folder path")
                folder = validated_folder
            except Exception as e:
                logger.error(f"Security validation failed for folder {folder}: {e}")
                raise HTTPException(status_code=403, detail="Invalid or dangerous folder path")
        
        # Search for existing connection
        if name:
            existing = await FileDataset.find_one(FileDataset.name == name)
        else:
            existing = await FileDataset.find_one(FileDataset.folder == folder)
            
        if existing:
            return existing
        
        # Create new connection
        connection = FileDataset(
            name=name if name else folder,
            type='file',
            folder=None if name else folder,
            inputType='file'
        )
        
        if folder:
            os.makedirs(os.path.dirname(folder), exist_ok=True)
        
        await connection.insert()
        return connection

    def getDfMongoContent(self, dataset: MongoDataset, datasetParams: DatasetParams, pagination: Pagination = None) -> NodeDataPandasDf:
        """Retrieve MongoDB dataset content"""
        from pymongo.mongo_client import MongoClient
        from pymongo.errors import ConnectionFailure
        from pymongoarrow.monkey import patch_all
        patch_all()
        
        client = None
        try:
            logger.info(f"Connecting to MongoDB dataset: {dataset.name}")
            logger.debug(f"MongoDB URI: {dataset.uri[:20]}... (truncated for security)")
            
            client = MongoClient(dataset.uri)
            db = client[dataset.database] if dataset.database else client[datasetParams.database]
            col = db[dataset.collection] if dataset.collection else db[datasetParams.table]
            
            if db is not None and col is not None:
                logger.debug(f"Querying collection: {col.name} in database: {db.name}")
                
                cursor = col.find({})
                total_docs = col.count_documents({})
                logger.info(f"Found {total_docs} documents in collection")
                
                if pagination and pagination.page and pagination.perPage:
                    skip = (pagination.page - 1) * pagination.perPage
                    cursor = cursor.skip(skip).limit(pagination.perPage)
                    logger.debug(f"Applied pagination: skip={skip}, limit={pagination.perPage}")
                
                df = pd.DataFrame(list(cursor))
                logger.info(f"Successfully retrieved {len(df)} records from MongoDB")
                
                schema = generate_pandas_schema(df)
                node_data = NodeDataPandasDf(
                    nodeSchema=schema,
                    name=dataset.collection if dataset.collection else datasetParams.table
                )
                
                if pagination:
                    node_data.dataExample = df.iloc[:pagination.perPage] if pagination.perPage else df
                else:
                    node_data.data = df
                    
                return node_data
            else:
                logger.error("Database and collection must be specified")
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                                  detail="Database and collection must be specified")
                                  
        except ConnectionFailure as err:
            logger.error(f"MongoDB connection failed for dataset {dataset.name}: {err}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                              detail=f"Database error: {err}")
        except PermissionError as err:
            logger.error(f"MongoDB permission error for dataset {dataset.name}: {err}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                              detail=f"Permission error: {err}")
        except Exception as e:
            logger.error(f"Unexpected error querying MongoDB dataset {dataset.name}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
        finally:
            if client:
                client.close()
                logger.debug("MongoDB connection closed")

    def getDfMysqlContent(self, dataset: MysqlDataset, datasetParams: DatasetParams, pagination: Pagination = None) -> NodeDataPandasDf:
        """Retrieve MySQL dataset content"""
        engine = None
        try:
            logger.info(f"Connecting to MySQL dataset: {dataset.name}")
            logger.debug(f"MySQL host: {dataset.host}, database: {dataset.database or datasetParams.database}")
            
            database = datasetParams.database if datasetParams.database else dataset.database
            table = datasetParams.table if datasetParams.table else dataset.table
            
            if database and table:
                connection_string = f"mysql+mysqlconnector://{dataset.user}:***@{dataset.host}/{database}"
                logger.debug(f"MySQL connection string: {connection_string}")
                
                engine = create_engine(f"mysql+mysqlconnector://{dataset.user}:{dataset.password}@{dataset.host}/{database}")
                
                if pagination and pagination.page and pagination.perPage:
                    offset = (pagination.page - 1) * pagination.perPage
                    query = f"SELECT * FROM {table} LIMIT {pagination.perPage} OFFSET {offset}"
                    logger.debug(f"MySQL query with pagination: {query}")
                else:
                    query = f"SELECT * FROM {table}"
                    logger.debug(f"MySQL query: {query}")
                
                result_dataFrame = pd.read_sql(query, engine)
                logger.info(f"Successfully retrieved {len(result_dataFrame)} records from MySQL")
                
                schema = generate_pandas_schema(result_dataFrame)    
                node_data = NodeDataPandasDf(
                    nodeSchema=schema,
                    name=dataset.name
                )
                if pagination:
                    node_data.dataExample = result_dataFrame
                else:
                    node_data.data = result_dataFrame
                return node_data
            else:
                logger.error(f"Database and table must be specified for dataset: {dataset.name}")
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                                  detail="Database and table must be specified")
                
        except mysql.connector.Error as err:
            logger.error(f"MySQL error for dataset {dataset.name}: {err}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                              detail=f"Database error: {err}")
        except PermissionError as err:
            logger.error(f"MySQL permission error for dataset {dataset.name}: {err}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                              detail=f"Permission error: {err}")
        except Exception as e:
            logger.error(f"Unexpected error querying MySQL dataset {dataset.name}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
        finally:
            if engine:
                engine.dispose()
                logger.debug("MySQL connection disposed")

    def getDfFileContentData(self, dataset: FileDataset, pagination: Pagination = None) -> NodeDataPandasDf:
        """Retrieve file dataset content"""
        try:
            logger.info(f"Reading file dataset: {dataset.name}")
        
            path = dataset.folder if dataset.folder else dataset.filePath
            logger.debug(f"Path: {path}")
            
            # SECURITY: Validate file path to prevent path traversal attacks
            if not path:
                raise HTTPException(status_code=400, detail="File path is required")
            
            try:
                validated_path = PathSecurityValidator.validate_file_path(path)
                # Additional check: verify path is within allowed directories
                allowed_dirs = SecurityConfig.get_allowed_base_directories()
                if not FileAccessController.can_read_file(validated_path, allowed_dirs):
                    raise HTTPException(status_code=403, detail=f"Access denied to path: {path}")
                path = validated_path
            except Exception as e:
                logger.error(f"Security validation failed for path {path}: {e}")
                raise HTTPException(status_code=403, detail="Access denied: Invalid or dangerous file path")
                            
            # Handle folder case
            if dataset.folder and dataset.folder != None:
                logger.debug("Processing folder dataset")
                if not os.path.exists(dataset.folder):
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Folder not found: {dataset.folder}")
                if not os.path.isdir(dataset.folder):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path is not a directory: {dataset.folder}")
                data = folder(path, pagination)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame(data.data)
            else:
                if not path or not os.path.exists(path):
                    logger.error(f"File not found: {path}")
                    raise HTTPException(status_code=404, detail="File not found")
                # Handle file case
                file_size = os.path.getsize(path)
                logger.debug(f"File size: {file_size} bytes")
                
                # CSV has special pagination handling (read-time optimization)
                if path.endswith('.csv'):
                    logger.debug("Reading CSV file")
                    if pagination and pagination.page and pagination.perPage:
                        skiprows = (pagination.page - 1) * pagination.perPage
                        logger.debug(f"CSV pagination: skiprows={skiprows}, nrows={pagination.perPage}")
                        df = pd.read_csv(path, 
                                        header=int(dataset.csvHeader) if dataset.csvHeader is not None else 0,
                                        delimiter=dataset.csvDelimiter or ',',
                                        skiprows=range(1, skiprows + 1) if skiprows > 0 else None,
                                        nrows=pagination.perPage)
                    else:
                        df = pd.read_csv(path, 
                                        header=int(dataset.csvHeader) if dataset.csvHeader is not None else 0,
                                        delimiter=dataset.csvDelimiter or ',')
                
                # All other formats: read first, then paginate
                elif path.endswith('.json'):
                    logger.debug("Reading JSON file")
                    df = pd.read_json(path)
                elif path.endswith(('.xlsx', '.xls')):
                    logger.debug("Reading Excel file")
                    df = pd.read_excel(path)
                elif path.endswith('.tsv'):
                    logger.debug("Reading TSV file")
                    df = pd.read_csv(path, header=int(dataset.csvHeader), sep='\t')
                elif path.endswith('.parquet'):
                    logger.debug("Reading Parquet file")
                    df = pd.read_parquet(path)
                elif path.endswith('.avro'):
                    logger.debug("Reading Avro file")
                    with open(path, 'rb') as fichier:
                        df = pd.DataFrame(reader(fichier))
                else:
                    logger.error(f"Unsupported file format: {path}")
                    raise HTTPException(status_code=400, detail="Unsupported file format")
                
                # Apply pagination for all non-CSV formats (post-read pagination)
                if not path.endswith('.csv') and pagination:
                    start_idx = (pagination.page - 1) * pagination.perPage
                    end_idx = start_idx + pagination.perPage
                    logger.debug(f"Post-read pagination: start={start_idx}, end={end_idx}")
                    df = df.iloc[start_idx:end_idx]
            
            logger.info(f"Successfully read {len(df)} records from file: {path}")
            
            schema = generate_pandas_schema(df)
            node_data = NodeDataPandasDf(
                nodeSchema=schema,
                name=dataset.name or os.path.basename(path)
            )
            
            if pagination:
                node_data.dataExample = df
            else:
                node_data.data = df
                
            return node_data
        except HTTPException:
            raise

        except PermissionError as err:
            logger.error(f"Permission error reading file {path}: {err}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                              detail=f"Permission error: {err}")
        except Exception as e:
            logger.error(f"Unexpected error reading file dataset {dataset.name}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    async def debug_database_connection(self):
        """Debug method to check database connection and collection"""
        try:
            # Vérifier la connexion directe à MongoDB
            from pymongo import AsyncMongoClient
            client = AsyncMongoClient("mongodb://localhost:27017")  # Votre URI
            db = client["daav_datasets"]
            collection = db["datasets"]
            
            # Compter les documents directement
            count = await collection.count_documents({})
            logger.info(f"Direct MongoDB count: {count} documents in datasets collection")
            
            # Lister quelques documents
            cursor = collection.find({}).limit(5)
            docs = await cursor.to_list(length=5)
            logger.info(f"Sample documents: {len(docs)} found")
            for doc in docs:
                logger.info(f"Document ID: {doc.get('_id')}, Name: {doc.get('name')}, Type: {doc.get('type')}")
            
            # Vérifier avec Beanie
            beanie_count = await Dataset.count()
            logger.info(f"Beanie count: {beanie_count} documents")
            
            return {
                "direct_count": count,
                "beanie_count": beanie_count,
                "sample_docs": len(docs)
            }
            
        except Exception as e:
            logger.error(f"Debug connection error: {e}", exc_info=True)
            raise




