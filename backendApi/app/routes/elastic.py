"""Elasticsearch-specific routes: cluster information, indices, mappings and queries.

Index deletion is deliberately not exposed.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.middleware.auth import CurrentUser
from app.models.interface.dataset_interface import ElasticDataset, _validate_es_index
from app.models.interface.node_data import NodeDataPandasDf
from app.services.dataset_service import DatasetService
from app.services.elastic_service import ElasticService
from app.services.user_service import UserService
from app.utils.utils import generate_pandas_schema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/datasets", tags=["elasticsearch"],
                   responses={404: {"description": "Not found"}})
dataset_service = DatasetService()
elastic_service = ElasticService()
user_service = UserService()

MAX_QUERY_SIZE = 100


class IndexRequest(BaseModel):
    index: str

    @field_validator('index', mode='before')
    @classmethod
    def validate_index(cls, v):
        if not v:
            raise ValueError("'index' is required")
        return _validate_es_index(v)


class CreateIndexRequest(IndexRequest):
    mappings: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


class QueryRequest(IndexRequest):
    # Query DSL clause (object or JSON string) or Lucene query string; empty = match all
    query: Optional[Any] = None
    fields: Optional[List[str]] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=MAX_QUERY_SIZE)
    includeId: bool = True


class QueryResponse(BaseModel):
    total: int
    data: List[Dict[str, Any]]


async def _get_elastic_dataset(dataset_id: str, user) -> ElasticDataset:
    dataset = await dataset_service.get_dataset(dataset_id, user)
    if not isinstance(dataset, ElasticDataset):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="The dataset is not an Elasticsearch dataset")
    return dataset


@router.get("/{dataset_id}/elastic/info")
async def cluster_info(dataset_id: str, current_user: CurrentUser) -> Dict[str, Any]:
    """Cluster name, version and health"""
    dataset = await _get_elastic_dataset(dataset_id, current_user)
    return await asyncio.to_thread(elastic_service.info, dataset)


@router.get("/{dataset_id}/elastic/indices")
async def list_indices(dataset_id: str, current_user: CurrentUser, includeHidden: bool = False) -> List[Dict[str, Any]]:
    """Indices visible with the dataset credentials, with document count, size and aliases"""
    dataset = await _get_elastic_dataset(dataset_id, current_user)
    return await asyncio.to_thread(elastic_service.list_indices, dataset, includeHidden)


@router.get("/{dataset_id}/elastic/indices/{index}/mapping")
async def get_mapping(dataset_id: str, index: str, current_user: CurrentUser) -> Dict[str, Any]:
    try:
        _validate_es_index(index)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    dataset = await _get_elastic_dataset(dataset_id, current_user)
    return await asyncio.to_thread(elastic_service.get_mapping, dataset, index)


@router.post("/{dataset_id}/elastic/indices", status_code=status.HTTP_201_CREATED)
async def create_index(dataset_id: str, request: CreateIndexRequest, current_user: CurrentUser) -> Dict[str, Any]:
    """Create an index (owner only)"""
    dataset = await _get_elastic_dataset(dataset_id, current_user)
    if not await user_service.can_modify_dataset(current_user, dataset_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await asyncio.to_thread(elastic_service.create_index, dataset, request.index,
                            request.mappings, request.settings)
    logger.info(f"User {current_user.username} created index {request.index} on dataset {dataset_id}")
    return {"index": request.index, "created": True}


@router.post("/{dataset_id}/elastic/query")
async def query_index(dataset_id: str, request: QueryRequest, current_user: CurrentUser) -> QueryResponse:
    """Run a query and return one page of documents with the total number of matches"""
    dataset = await _get_elastic_dataset(dataset_id, current_user)
    data, total = await asyncio.to_thread(
        elastic_service.search_page, dataset, request.index, request.page, request.size,
        request.query, request.includeId, request.fields
    )
    return QueryResponse(total=total, data=data)


@router.post("/{dataset_id}/elastic/sample")
async def sample(dataset_id: str, request: QueryRequest, current_user: CurrentUser) -> NodeDataPandasDf:
    """Sample of a query as node data, used to preview the Elasticsearch input node"""
    dataset = await _get_elastic_dataset(dataset_id, current_user)
    df = await asyncio.to_thread(
        elastic_service.sample_dataframe, dataset, request.index, request.size,
        request.query, request.fields, request.includeId
    )
    node_data = NodeDataPandasDf(nodeSchema=generate_pandas_schema(df), name=request.index)
    node_data.dataExample = df
    return node_data
