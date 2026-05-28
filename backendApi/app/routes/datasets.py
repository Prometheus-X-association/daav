import logging
import traceback
from fastapi import APIRouter, Body, HTTPException, Request, status, UploadFile, Depends
import httpx
from app.config.security import SecurityConfig
from app.middleware.auth import CurrentUser
from app.middleware.security import log_file_access
from app.models.interface.dataset_interface import DatasetContentResponse, DatasetUnion, ConnectionInfo, DatasetParams, PTXDataset, Pagination, Dataset, MySQLContentResponse, MysqlDataset, MongoContentResponse, MongoDataset, ElasticContentResponse, ElasticDataset, ApiContentResponse, ApiDataset, FileContentResponse, FileDataset
import xml.etree.ElementTree as ET
import base64
import json
import os
import pandas as pd
import jsonschema
from app.models.interface.node_data import NodeDataPandasDf, NodeDataUnion
from app.services.dataset_service import DatasetService
from app.utils.utils import folder, generate_pandas_schema
from app.utils.security import FileAccessController, PathSecurityValidator
from pathlib import Path
from app.config.settings import settings
from app.utils.utils import json_api_schema, custom_api_schema



logger = logging.getLogger(__name__)
router = APIRouter(prefix="/datasets",
                   tags=["datasets"], responses={404: {"description": "Not found"}})
dataset_service = DatasetService()

UPLOAD_DIR = Path(settings.upload_dir)

@router.get("/")
async def get_all_datasets(current_user: CurrentUser):
    """Get all datasets accessible by current user"""
    try:
        logger.info(f"User {current_user.username} fetching datasets")
        datasets = await dataset_service.get_datasets(current_user)

        logger.info(f"Successfully returned {len(datasets)} datasets to user {current_user.username}")
        return datasets
    except Exception as e:
        logger.error(f"Error fetching datasets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{id}")
async def get_dataset(id: str, current_user: CurrentUser) -> Dataset:
    """Get a single dataset with permission check"""
    return await dataset_service.get_dataset(id, current_user)

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, current_user: CurrentUser):
    """Delete a dataset with permission check"""
    try:
        logger.info(f"User {current_user.username} deleting dataset: {dataset_id}")
        success = await dataset_service.delete_dataset(dataset_id, current_user)
        
        if success:
            logger.info(f"User {current_user.username} successfully deleted dataset: {dataset_id}")
            return {"message": "Dataset deleted successfully"}
        else:
            logger.warning(f"Failed to delete dataset: {dataset_id}")
            raise HTTPException(status_code=404, detail="Dataset not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/")
async def edit_dataset(dataset: DatasetUnion, current_user: CurrentUser) -> bool:
    """Edit a dataset with permission check"""
    return await dataset_service.edit_dataset(dataset, current_user)

@router.post("/")
async def create_dataset(dataset: DatasetUnion, current_user: CurrentUser):
    """Create a new dataset with ownership assignment"""
    try:
        logger.info(f"User {current_user.username} creating new dataset: {dataset.name} (Type: {dataset.type})")
        result = await dataset_service.add_connection(dataset, current_user)
        
        if result["status"] == "Connection added":
            logger.info(f"User {current_user.username} successfully created dataset: {dataset.name}")
        else:
            logger.warning(f"Dataset creation failed: {result['status']}")
            
        return result
    except Exception as e:
        logger.error(f"Error creating dataset {dataset.name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/uploadFile")
async def receive_file(
    file: list[UploadFile] | UploadFile,
    current_user: CurrentUser,
    folder: str = None
) -> list:
    """Upload one or multiple files using the configured upload directory with security validation"""
    try:
        logger.info(f"User {current_user.username} uploading file(s)")
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Si file est une liste, on boucle, sinon on le met dans une liste
        files = file if isinstance(file, list) else [file]
        results = []

        for f in files:
            result = await _save_upload_file(f, current_user, folder)
            results.append(result)

        # Retourne la liste si plusieurs fichiers, sinon un seul dict
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file(s): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload file(s): {str(e)}")

async def _save_upload_file(file: UploadFile, current_user: CurrentUser, folder: str = None) -> dict:
    """Traitement et sauvegarde d'un seul fichier UploadFile avec isolation par utilisateur"""
    # Validation de sécurité du nom de fichier
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    safe_filename = PathSecurityValidator.validate_filename(file.filename)

    if not PathSecurityValidator.validate_file_extension(safe_filename):
        raise HTTPException(
            status_code=400,
            detail=f"File extension not allowed. Allowed extensions: {PathSecurityValidator.ALLOWED_EXTENSIONS}"
        )

    filename_parts = safe_filename.split('/')
    final_filename = filename_parts[-1]

    # create folder per user (user_id) to isolate files
    user_dir = UPLOAD_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # If an additional folder is specified (folder parameter)
    if folder:
        safe_folder = PathSecurityValidator.validate_filename(folder)
        if '..' in safe_folder or safe_folder.startswith('/') or safe_folder.startswith('\\'):
            raise HTTPException(status_code=400, detail="Invalid folder name")
        sub_dir = user_dir / safe_folder
        sub_dir.mkdir(exist_ok=True)
        base_dir = sub_dir
    # If the filename contains a path (old behavior for compatibility)
    elif len(filename_parts) > 1:
        dir_name = filename_parts[0]
        safe_dir_name = PathSecurityValidator.validate_filename(dir_name)
        if '..' in safe_dir_name or safe_dir_name.startswith('/') or safe_dir_name.startswith('\\'):
            raise HTTPException(status_code=400, detail="Invalid directory name")
        sub_dir = user_dir / safe_dir_name
        sub_dir.mkdir(exist_ok=True)
        base_dir = sub_dir
    else:
        base_dir = user_dir

    filepath = base_dir / final_filename

    try:
        validated_path = PathSecurityValidator.validate_file_path(str(filepath), str(UPLOAD_DIR))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file path: {str(e)}")

    content = await file.read()
    max_file_size = settings.max_file_size
    if len(content) > max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(content)} bytes (max: {max_file_size})"
        )

    with open(validated_path, 'wb') as f:
        f.write(content)

    logger.info(f"User {current_user.username} uploaded file successfully: {validated_path}")
    result = {"filepath": str(validated_path), "user_dir": str(user_dir)}
    if base_dir != user_dir:
        result["folder"] = str(base_dir)
    return result

@router.post("/getContentDataset", response_model=DatasetContentResponse)
async def getContentDataset(request: Request, data: ConnectionInfo, current_user: CurrentUser) -> DatasetContentResponse:
    """Get dataset content with permission check"""
    connection = data.dataset

    # If the frontend sends a dataset id, reload the full stored dataset from DB.
    # This preserves sensitive fields like PTX token/refreshToken and avoids relying on partial front-end payload.
    if hasattr(connection, 'id') and connection.id:
        connection = await dataset_service.get_dataset(connection.id, current_user)

    pagination = data.pagination
    datasetParams = data.datasetParams
    if isinstance(connection, FileDataset):
        client_ip = request.client.host
        file_path = connection.folder if connection.folder else connection.filePath
        log_file_access(client_ip, file_path, "read")
        try:
            result  = getFileContent(connection, pagination)            
        except PermissionError as e:
            log_file_access(client_ip, file_path, "read_failed")
        return result
    elif isinstance(connection, MongoDataset):    
        return getMongoContent(connection, pagination, datasetParams)
    elif isinstance(connection, MysqlDataset):
        return getMysqlContent(connection, pagination, datasetParams)
    elif isinstance(connection, ApiDataset):
        return await getApiContent(connection, pagination)
    elif  isinstance(connection, ElasticDataset):
        return getElasticContent(connection, pagination, datasetParams)
    elif  isinstance(connection, PTXDataset):
        return getPTXContent(connection, pagination, datasetParams)
    else :
        raise ValueError("Type de connexion non reconnu")
    
@router.post("/getDfContentDataset", response_model=NodeDataUnion)
async def getDfContentDataset(request: Request, data: ConnectionInfo, current_user: CurrentUser) -> NodeDataPandasDf:
    """Get dataset dataframe content with permission check"""
    connection = data.dataset

    # If the frontend sends a dataset id, reload the full stored dataset from DB.
    # This preserves sensitive internal fields for the backend execution path.
    if hasattr(connection, 'id') and connection.id:
        connection = await dataset_service.get_dataset(connection.id, current_user)

    pagination = data.pagination
    datasetParams = data.datasetParams
    if isinstance(connection, FileDataset):
        client_ip = request.client.host
        file_path = connection.folder if connection.folder else connection.filePath
        log_file_access(client_ip, file_path, "read")
        try:
            result  = dataset_service.getDfFileContentData(connection, pagination )            
        except PermissionError as e:
            log_file_access(client_ip, file_path, "read_failed")
        return result
    elif isinstance(connection, MongoDataset):    
        return dataset_service.getDfMongoContent(connection,datasetParams, pagination )
    elif isinstance(connection, MysqlDataset):
        return dataset_service.getDfMysqlContent(connection,datasetParams, pagination)
    elif isinstance(connection, ApiDataset):
        raise ValueError("Dataset type not handle")     
    elif  isinstance(connection, ElasticDataset):
       raise ValueError("Dataset type not handle") 
    else :
        raise ValueError("Dataset type not handle")
    
@router.post("/getDfFromJson" ,response_model=NodeDataUnion)
def getDfFromJson(data: dict)-> NodeDataPandasDf:
    print("data", data)
    json_data = data['data']
    if not json_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided data is empty.")
    try:
        df = pd.DataFrame(json_data)
        schema = generate_pandas_schema(df)
        node_data = NodeDataPandasDf(
                        nodeSchema=schema,
                        name="example",
                        dataexamples=df,
                    )
        #print(node_data)
        # Return the NodeDataPandasDf object
        return node_data
    except Exception as err:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing data: {err}")


async def mysql_content(
    dataset: MysqlDataset ,
    pagination: Pagination = Body(..., examples={
        "page": 1,
        "perPage": 10
    }),
    datasetParams: DatasetParams = Body(..., examples={
        "default": {
            "summary": "Dataset parameters example",
            "value": {
                "database": "test_db",
                "table": "test_table"
            }
        }
    })
) -> MySQLContentResponse:
    """
    Retrieve MySQL content based on the provided connection details, pagination, and dataset parameters.

    Returns:
        MySQLContentResponse: A dictionary containing the following keys:
            - databases: List of database names (if no database is specified).
            - tables: List of table names (if no table is specified).
            - table_description: List of dictionaries describing the table columns.
            - data: List of dictionaries containing the table data.
            - total_rows: Total number of rows in the table.
            - limit: The maximum number of rows displayed.
            - current_page: Current page number.

    """
    return getMysqlContent(dataset, pagination, datasetParams)

import mysql.connector 
from mysql.connector import cursor
def getAll(cursor: cursor):
    cursor.execute("SHOW DATABASES")
    db_list = [
        db["Database"].decode() if isinstance(db["Database"], (bytes, bytearray)) else db["Database"]
        for db in cursor.fetchall()
    ]
    # Exclure les bases systèmes
    system_dbs = {'performance_schema', 'information_schema', 'mysql', 'sys'}
    db_list = [db for db in db_list if db not in system_dbs]
    tables_list = []
    for db in db_list:   
        tables = getTables(cursor, db)
        tables_list.append(tables)
    return db_list, tables_list

def getTables(cursor: cursor, database_name: str) -> list[str]:
        cursor.execute(f"USE {database_name}")
        cursor.execute("SHOW TABLES")  
        tables_list = [table[f"Tables_in_{database_name}"] for table in cursor.fetchall()]
        return tables_list

def getMysqlContent(dataset: MysqlDataset, pagination: Pagination, datasetParams: DatasetParams) -> MySQLContentResponse:
    try:        
        database_name = dataset.database if dataset.database else None
        conn = mysql.connector.connect(
            host=dataset.host,
            user=dataset.user,
            password=dataset.password,
            auth_plugin='mysql_native_password'
        )
        cursor = conn.cursor(dictionary=True)

        db_list = None
        tables_list = None
        if not dataset.database and not datasetParams.database:
            db_list, tables_list = getAll(cursor)
            return MySQLContentResponse(
                databases=db_list,
                tables=tables_list,
                data=[]
            )

        if not dataset.table and not datasetParams.table:
            database = datasetParams.database if datasetParams.database else dataset.database
            tables_list = getTables(cursor, database)
            return MySQLContentResponse(
                tables=tables_list,
                data=[]
            )
        
        if dataset.database or datasetParams.database and dataset.table or datasetParams.table:
            if datasetParams.database:
                database_name = datasetParams.database

            cursor.execute(f"USE {database_name}")
            table_name = dataset.table if dataset.table else datasetParams.table
            cursor.execute(f"DESCRIBE {table_name}")
            table_description = cursor.fetchall()

            # Get total rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()['COUNT(*)']

            # Get table content with pagination
            offset = (pagination.page - 1) * pagination.perPage
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {pagination.perPage} OFFSET {offset}")

            table_content = cursor.fetchall()

            return MySQLContentResponse(
                table_description=table_description,
                data=table_content,
                total_rows=row_count,
                current_page=offset,
                limit=pagination.perPage
            )

    except mysql.connector.Error as err:
        print(err)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Database error: {err}")
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

async def mongo_content(
    dataset: MongoDataset ,
    pagination: Pagination = Body(..., examples={
        "page": 1,
        "perPage": 10
    }),
    datasetParams: DatasetParams = Body(..., examples={
        "default": {
            "summary": "Dataset parameters example",
            "value": {
                "database": "test_db",
                "collection": "test_collection"
            }
        }
    })
) -> MongoContentResponse:
    """
    Retrieve MongoDB content based on the provided connection details, pagination, and dataset parameters.

    Returns:
        MongoContentResponse: A dictionary containing the following keys:
            - databases: List of database names (if no database is specified).
            - collections: List of collection names (if no collection is specified).
            - data: List of dictionaries containing the collection data.
            - total_rows: Total number of rows in the collection.
            - limit: The maximum number of rows displayed.
            - current_page: Current page number.
    """
    return getMongoContent(dataset, pagination, datasetParams)

def rem_ObjectId(item):
    import bson 
    if hasattr(item, 'items'): 
        for k, v in item.items(): 
            if type(v) == bson.objectid.ObjectId:  
                yield k
            if isinstance(v, dict):
                for result in rem_ObjectId(v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in rem_ObjectId(d):
                        yield result

#convertir l'id en string
def serialize_id(document: dict) -> dict:
    from dict_path_finder import find_paths_by_key
    from benedict import benedict
    import json

    # get all ObjectId values
    data = benedict(document, keypath_separator=None)
    key_list = []
    for key in rem_ObjectId(document):
        if not key in key_list:
            key_list.append(key)

    # get all ObjectId path 
    for key in key_list:
        results = find_paths_by_key(document, key)
        for result in results:
            replace = str.maketrans('[]"', '   ', ']"')
            result = result.translate(replace)
            path = result[5:].split(' ')
 
            # transform numeric string into int for list index
            for index, key in enumerate(path):
                if key.isnumeric():
                    path[index] = int(path[index])

            # convert ObjectId into str
            data[path] = str(data[path])
    document = json.loads(data.to_json())
    return document

#connexion à MongoDB
def getMongoContent(dataset: MongoDataset, pagination: Pagination, datasetParams: DatasetParams) -> MongoContentResponse:
    from pymongo.mongo_client import MongoClient
    from pymongo.errors import ConnectionFailure
    try:
        client = MongoClient(dataset.uri)
        collections = []
        # For multiple db and collection
        if not dataset.database and not datasetParams.database:
            databases = client.list_database_names()
            if 'config' in databases: databases.remove('config')
            db = client[datasetParams.database] if datasetParams.database else client[databases[0]]
            for database in databases:
                db_list = client[database]
                collections.append(db_list.list_collection_names())
                col = db[datasetParams.table] if datasetParams.table else None    
            return MongoContentResponse(
                databases=databases,
                collections=collections,
                data=[]
            )    
        
        # For a single db but multiple collection
        if not dataset.collection and not datasetParams.table:
            db = client[dataset.database] if dataset.database else client[datasetParams.database]
            collections = db.list_collection_names()
            col = db[datasetParams.table] if datasetParams.table else db[collections[0]]
            return MongoContentResponse(
                collections=collections,
                data=[]
            )

        # For a single collection
        if dataset.database or datasetParams.database and dataset.collection or datasetParams.table:
            db = client[dataset.database] if dataset.database else client[datasetParams.database]
            col = db[dataset.collection] if dataset.collection else db[datasetParams.table]
            if col is None:
                dataset = {"result": [], "total": 0, "limit": 1, "offset": 0}
            else:
                offset = (pagination.page * pagination.perPage) - pagination.perPage
                limit = pagination.perPage
                all_traces = list(col.find({}).skip(offset).limit(limit))
                total = col.count_documents({})    
        
                result = [serialize_id(doc) for doc in all_traces]
                dataset = {"result": result, "total": total, "limit": limit, "offset": offset}
            return MongoContentResponse(
                data=dataset['result'],
                total_rows=dataset['total'],
                limit=dataset['limit'],
                current_page=dataset['offset']
            )
    except  ConnectionFailure as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Database error: {err}")
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission error: {err}")
    finally:
        client.close()


async def elastic_content(
    dataset: ElasticDataset,
    pagination: Pagination = Body(..., examples={
        "page": 1,
        "perPage": 10
    }),
    datasetParams: DatasetParams = Body(..., examples={
        "default": {
            "summary": "Dataset parameters example",
            "value": {
                "database": "test_db",
                "collection": "test_collection"
            }
        }
    })
) -> ElasticContentResponse:
    """
    Retrieve Elasticsearch content based on the provided connection details, pagination, and dataset parameters.

    Returns:
        ElasticContentResponse: A dictionary containing the following keys:
            - indices: List of indices names (if no index is specified).
            - data: List of dictionaries containing the index data.
            - total_rows: Total number of rows in the index.
            - limit: The maximum number of rows displayed.
            - current_page: Current page number.
    """
    return getElasticContent(dataset, pagination, datasetParams)

def getElasticContent(dataset: ElasticDataset, pagination: Pagination, datasetParams: DatasetParams) -> ElasticContentResponse:
    from elasticsearch import Elasticsearch, ApiError
    try:
        if dataset.key:
            client = Elasticsearch(dataset.url, api_key=dataset.key)
        elif dataset.user and dataset.password:
            client = Elasticsearch(dataset.url, basic_auth=(dataset.user, dataset.password))
        elif dataset.bearerToken:
            client = Elasticsearch(dataset.url, bearer_auth=dataset.bearerToken)

        client.indices.refresh(index=dataset.index)
        total = client.cat.count(index=dataset.index, params={"format": "json"})   
        offset = (pagination.page * pagination.perPage) - pagination.perPage     
        
        if not dataset.index and not datasetParams.table:
            indices = client.cat.indices(h='index', s='index').split();      
            client.transport.close()
            return ElasticContentResponse(
                indices=indices,
                data=[]
            )
        
        if dataset.index or datasetParams.table:
            resp = client.search(index=dataset.index, from_=offset, size="100", query={"match_all": {}})
            hits = resp['hits']['hits']
            data = []
            for item in hits:
                data.append(item['_source'])
            client.transport.close()
            return ElasticContentResponse(
                data=data,
                total_rows=total[0]['count'],
                limit=pagination.perPage,
                current_page=(pagination.page * pagination.perPage) - pagination.perPage
            )

    except ApiError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Database error: {err}")
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission error: {err}")
def getPTXContent(dataset: PTXDataset, pagination: Pagination, datasetParams: DatasetParams):

    return dataset

async def api_content(
    dataset: ApiDataset ,
    pagination: Pagination = Body(..., examples={
        "page": 1,
        "perPage": 10
    }),
    datasetParams: DatasetParams = Body(..., examples={
        "default": {
            "summary": "Dataset parameters example",
            "value": {
                "database": "test_db",
                "collection": "test_collection"
            }
        }
    })
) -> ApiContentResponse:
    """
    Retrieve Api content based on the provided connection details, pagination, and dataset parameters.

    Returns:
        ApiContentResponse: A dictionary containing the following keys:
            - data: List of dictionaries containing the api data.
            - total_rows: Total number of rows in the api.
            - limit: The maximum number of rows displayed.
            - current_page: Current page number.
    """
    return await getApiContent(dataset, pagination, datasetParams)

def apiContent(response: str) -> list:
    if 'json' in response.headers['Content-Type']:
        data = response.json()  
        donnees = list(data.items())
    else:
        content = response.content
        tree = ET.fromstring(content)

        donnees = []
        for child in tree:
            row = {}
            for field in child:
                row[field.tag] = field.text
            donnees.append(row)
    return donnees

async def getApiContent(connection: ApiDataset, pagination: Pagination) -> ApiContentResponse:
    try:
        API_URL = pagination.nextUrl if getattr(pagination, "nextUrl", None) else connection.url
        headers = {}
        if connection.apiAuth == "bearer":
            headers = { "Authorization" : f"token {connection.bearerToken}" }
        elif connection.apiAuth == "oauth2":
            authBody = "grant_type=client_credentials"
            encode_token = connection.basicToken.encode("utf-8")
            base64_bytes = base64.b64encode(encode_token)
            base64_token = base64_bytes.decode('utf-8')
            authHeaders = {'Authorization': f"Basic {base64_token}"}
            async with httpx.AsyncClient() as client:
                authRequest = await client.post(connection.authUrl, data=authBody, headers=authHeaders)
                if authRequest.status_code != 200:
                    authRequest = await client.get(connection.authUrl, headers=authHeaders)
                    if authRequest.status_code != 200:
                        raise HTTPException(status_code=authRequest.status_code, detail=f"Authentication error: {authRequest.text}")
                authRequest.raise_for_status()
               
            authResponse = authRequest.json()
            access_token = authResponse.get('access_token')
            headers = {'access_token': access_token,'authorization': f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL, headers=headers)
            response.raise_for_status() 
        content_type = response.headers.get("Content-Type", "")
        if "json" in content_type:
            data = response.json()
            # Detection JSON:API
            try:
                jsonschema.validate(instance=data, schema=json_api_schema)
                items = data["data"] if isinstance(data["data"], list) else [data["data"]]
                total = data.get("meta", {}).get("count") or data.get("meta", {}).get("total") or len(items)
                next_url = data.get("links", {}).get("next")
                prev_url = data.get("links", {}).get("prev")
                return ApiContentResponse(
                    data=items,
                    total_rows=total,
                    limit=len(items),
                    current_page=pagination.page,
                    next_url=next_url,
                    prev_url=prev_url
                )
            except jsonschema.ValidationError:
                pass
            # Detection custom_api
            try:
                jsonschema.validate(instance=data, schema=custom_api_schema)
                items = data["data"]
                total = data.get("count", len(items))
                next_url = data.get("next", {}).get("href") if data.get("next") else None
                prev_url = data.get("previous", {}).get("href") if data.get("previous") else None
                return ApiContentResponse(
                    data=items,
                    total_rows=total,
                    limit=len(items),
                    current_page=pagination.page,
                    next_url=next_url,
                    prev_url=prev_url
                )
            except jsonschema.ValidationError:
                pass
            # Fallback
            donnees = list(data.items()) if isinstance(data, dict) else data
        else:
            donnees = apiContent(response)

        return ApiContentResponse(
            data=donnees,
            total_rows=len(donnees),
            limit=pagination.perPage,
            current_page=pagination.page
        )
    except httpx.HTTPStatusError as err:
        raise HTTPException(status_code=err.response.status_code, detail=f"HTTP error: {err}")
    except httpx.ConnectError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connection error: {err}")
    except httpx.ReadTimeout as err:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"Timeout error: {err}")
    except httpx.RequestError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request error: {err}")
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission error: {err}")

import pandas as pd
from fastapi.responses import JSONResponse

def toRow (dataset: dict, donnees: list):
    data = dataset
    first_item = list(data)[0]
    item_len = len(data[first_item])

    for index, i in enumerate(range(0, item_len)):
        item = {}  
        for key in data:
            item[key] = data[key][index]
        donnees.append(item)



#lecture du fichier json
def JSONFile(file: str) -> JSONResponse:
    with open(file, 'r') as fichier:
        donnees = json.load(fichier)
    return donnees

#lecture du fichier format colone
def ColFile(file: str) -> list:
    import pyarrow.parquet as pq
    import pyarrow.feather as pf
    import pyarrow.orc as po
    donnees = []        
    if file.endswith('.parquet'):
        dataset = pq.read_table(file).to_pydict()
        toRow(dataset, donnees)
    elif file.endswith('.feather'):
        dataset = pf.read_table(file).to_pydict()
        toRow(dataset, donnees)
    elif file.endswith('.orc'):
        dataset = po.read_table(file).to_pydict()
        toRow(dataset, donnees)
    del dataset
    return donnees

#lecture du fichier XLS
def XLSFile(file: str) -> list:
    donnees = []      
    dataset = pd.read_excel(file).to_dict()
    toRow(dataset, donnees)   
    del dataset    
    return donnees    

#lecture du fichier Avro
def AvroFile(file: str) -> list:
    from fastavro import reader
    donnees = []        
    with open(file, 'rb') as fichier:
        avro_reader = reader(fichier)
        dataset = pd.DataFrame(avro_reader).to_dict()
        toRow(dataset, donnees)
        del dataset
    return donnees

#lecture du fichier XML
def XMLFile(file: str) -> list:
    tree = ET.parse(file)
    root = tree.getroot()
    donnees = []
    for child in root:
        row = {}
        for field in child:
            row[field.tag] = field.text
        donnees.append(row)
    return donnees

#lecture du fichier csv
def CSVFile(filePath: str, csvHeader: str, csvDelimiter: str) -> list:
    import csv
    from detect_delimiter import detect
    with open(filePath, mode='r', encoding='utf-8') as fichier:
        # detect csv delimiter
        if csvDelimiter == '':                                                
            delimiter = detect(fichier.readline(), default=",")
        elif filePath.endswith('.tsv'):
            delimiter = "\t"
        else:
            delimiter = csvDelimiter                
        fichier.seek(0)

        if csvHeader == "false":
            column_count = list(csv.reader(fichier, delimiter=delimiter))
            fichier.seek(0)
            column_name = []
            counter = 0
            for x in range(len(column_count[0])):
                counter += 1
                column_name.append('None' + str(counter))
        else:
            column_name = None

        # add header if not present
        donnees = []
        line_count = 0
        reader = csv.DictReader(fichier, delimiter=delimiter, fieldnames=column_name, restval=(0))    
        for row in reader:
            if line_count >= 100:
                break
            parsed_row = {}
            for key, value in row.items():
                try:
                    # Essayer de convertir en int, puis en float, sinon garder la chaîne                                       
                    parsed_row[key] = int(value)
                except ValueError:
                    try:
                        parsed_row[key] = float(value)
                    except ValueError:
                        # Gérer les booléens (true, false, True, False, etc.)
                        if value.lower() == 'true':
                            parsed_row[key] = True
                        elif value.lower() == 'false':
                            parsed_row[key] = False
                        else:
                            # Si ce n'est pas un nombre, un float ou un booléen, gardez la chaîne
                            parsed_row[key] = value
            donnees.append(parsed_row)
            line_count += 1
    return donnees


def getFileContent(connection: FileDataset, pagination: Pagination = None) -> FileContentResponse:
    try:
        data = []
        columnarFile = ('.parquet', '.feather', '.orc')

        if connection.folder and connection.folder != None:
            if not os.path.exists(connection.folder):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Folder not found: {connection.folder}")
            if not os.path.isdir(connection.folder):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path is not a directory: {connection.folder}")
            data = folder(connection.folder,pagination)
            if isinstance(data, FileContentResponse):
                return data
        else:
            validated_filePath = PathSecurityValidator.validate_file_path(connection.filePath)
             # Get allowed directories list (including dynamic upload_dir)
            allowed_base_dirs = SecurityConfig.get_allowed_base_directories()
            if not FileAccessController.can_read_file(validated_filePath, allowed_base_dirs):
                raise PermissionError(f"Access denied to directory: {validated_filePath}")
            if not connection.filePath:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File path is required")
            if not os.path.exists(connection.filePath):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {connection.filePath}")
            
            if not os.path.isfile(connection.filePath):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path is not a file: {connection.filePath}")

            if connection.filePath.endswith('.json'):
                data = JSONFile(connection.filePath)
            elif connection.filePath.endswith('.csv') or connection.filePath.endswith('.tsv'):
                data = CSVFile(connection.filePath, connection.csvHeader, connection.csvDelimiter)
            elif connection.filePath.endswith(columnarFile):
                data = ColFile(connection.filePath)    
            elif connection.filePath.endswith('.xls') or connection.filePath.endswith('.xlsx'):
                data = XLSFile(connection.filePath)    
            elif connection.filePath.endswith('.avro'):
                data = AvroFile(connection.filePath)  
            elif connection.filePath.endswith('.xml'):
                data = XMLFile(connection.filePath)
            elif connection.filePath.endswith('.txt'):
                with open(connection.filePath, 'r', encoding='utf-8') as f:
                    data = [{"text": f.read()}]    
            elif any(connection.filePath.lower().endswith(ext) for ext in [
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',
                '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma',
                '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'
            ]):
                import mimetypes
                import base64
                stats = os.stat(connection.filePath)
                max_size = settings.max_file_size
                if stats.st_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Media file too large: {stats.st_size} bytes (max: {max_size})"
                    )
                with open(connection.filePath, "rb") as media_file:
                    encoded = base64.b64encode(media_file.read()).decode('utf-8')
                mime_type, _ = mimetypes.guess_type(connection.filePath)
                data = [{
                    "media": encoded,
                    "file": os.path.basename(connection.filePath),
                    "mime_type": mime_type or "application/octet-stream",
                    "size": stats.st_size,
                    "path": connection.filePath
                }]
            else:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"File format not supported: {os.path.splitext(connection.filePath)[1]}")
        
        return FileContentResponse(
            data=data,
            total_rows=len(data),
            limit=pagination.perPage,
            current_page=(pagination.page * pagination.perPage) - pagination.perPage
        )
    except HTTPException:
        import traceback
        traceback.print_exc()
        raise    
    except FileNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {err}")
    except NotADirectoryError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Directory not found: {err}")
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission error: {err}")
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Can't read JSON file: {err}")
    except Exception as err:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {err}")

