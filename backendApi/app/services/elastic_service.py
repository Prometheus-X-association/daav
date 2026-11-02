"""Elasticsearch access for datasets, workflow nodes and the Elasticsearch dashboard."""
import json
import logging
import math
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

import numpy as np
import pandas as pd
from elasticsearch import (
    ApiError,
    AuthenticationException,
    AuthorizationException,
    BadRequestError,
    ConflictError,
    ConnectionError as EsConnectionError,
    Elasticsearch,
    NotFoundError,
    helpers,
)

from app.models.interface.dataset_interface import ElasticDataset, _validate_es_index
from app.utils.ssrf import SsrfError, ensure_public_url

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
PIT_KEEP_ALIVE = "2m"
SCAN_BATCH_SIZE = 1000
BULK_CHUNK_SIZE = 500
MAX_REPORTED_BULK_ERRORS = 5


class ElasticServiceError(Exception):
    """Error raised by ElasticService, carrying the HTTP status to return to the client.

    Elasticsearch authentication/authorization failures are reported as 502 (bad gateway):
    a 401/403 would be mistaken by the frontend for a DAAV session problem.
    """

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _error_reason(err: ApiError) -> str:
    body = err.body if isinstance(err.body, dict) else {}
    error = body.get('error')
    if isinstance(error, dict):
        root = (error.get('root_cause') or [{}])[0]
        return root.get('reason') or error.get('reason') or str(err)
    return str(error or err)


def parse_query(query: Any) -> Dict[str, Any]:
    """Build an Elasticsearch query clause from user input.

    Accepted inputs:
    - None or empty string: match all documents
    - a JSON object (string or dict): a Query DSL clause, optionally wrapped in {"query": ...}
    - any other string: a Lucene query_string, e.g. 'category:books AND price:>20'
    """
    if query is None or (isinstance(query, str) and not query.strip()):
        return {"match_all": {}}
    if isinstance(query, str):
        text = query.strip()
        if not text.startswith('{'):
            return {"query_string": {"query": text}}
        try:
            query = json.loads(text)
        except json.JSONDecodeError as e:
            raise ElasticServiceError(f"Invalid JSON query: {e}", 400)
    if isinstance(query, dict) and set(query) == {"query"} and isinstance(query["query"], dict):
        query = query["query"]
    if not isinstance(query, dict) or len(query) != 1:
        raise ElasticServiceError(
            'The query must contain exactly one clause, e.g. {"match": {"field": "value"}}', 400
        )
    return query


def hits_to_records(hits: Iterable[dict], include_id: bool = True) -> List[dict]:
    records = []
    for hit in hits:
        source = hit.get('_source') or {}
        records.append({'_id': hit['_id'], **source} if include_id else dict(source))
    return records


def to_json_safe(value: Any) -> Any:
    """Convert pandas/numpy values to types Elasticsearch accepts (NaN/NaT become null)."""
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, dict):
        return {str(k): to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [to_json_safe(v) for v in value]
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def infer_mappings(df: pd.DataFrame) -> Dict[str, Any]:
    """Explicit mappings for typed columns; other columns are left to dynamic mapping."""
    properties = {}
    for column, dtype in df.dtypes.items():
        if column == '_id':
            continue
        if pd.api.types.is_bool_dtype(dtype):
            properties[str(column)] = {"type": "boolean"}
        elif pd.api.types.is_integer_dtype(dtype):
            properties[str(column)] = {"type": "long"}
        elif pd.api.types.is_float_dtype(dtype):
            properties[str(column)] = {"type": "double"}
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            properties[str(column)] = {"type": "date"}
    return {"properties": properties}


class ElasticService:

    @staticmethod
    def _auth_kwargs(dataset: ElasticDataset) -> Dict[str, Any]:
        mode = dataset.authMode
        if mode is None:
            if dataset.key:
                mode = 'apiKey'
            elif dataset.user and dataset.password:
                mode = 'basic'
            elif dataset.bearerToken:
                mode = 'bearer'
            else:
                mode = 'none'
        if mode == 'apiKey':
            if not dataset.key:
                raise ElasticServiceError("The API key is missing", 400)
            return {"api_key": dataset.key}
        if mode == 'basic':
            if not (dataset.user and dataset.password):
                raise ElasticServiceError("The user name or password is missing", 400)
            return {"basic_auth": (dataset.user, dataset.password)}
        if mode == 'bearer':
            if not dataset.bearerToken:
                raise ElasticServiceError("The bearer token is missing", 400)
            return {"bearer_auth": dataset.bearerToken}
        return {}

    @contextmanager
    def connect(self, dataset: ElasticDataset) -> Iterator[Elasticsearch]:
        """Open a client for the dataset, translating errors into ElasticServiceError."""
        if not dataset.url:
            raise ElasticServiceError("The Elasticsearch URL is not set", 400)
        try:
            ensure_public_url(dataset.url)
        except SsrfError as e:
            raise ElasticServiceError(str(e), 400)

        kwargs: Dict[str, Any] = {
            "request_timeout": REQUEST_TIMEOUT,
            "verify_certs": dataset.verifyCerts is not False,
            **self._auth_kwargs(dataset),
        }
        client = Elasticsearch(dataset.url, **kwargs)
        try:
            yield client
        except ElasticServiceError:
            raise
        except EsConnectionError as e:
            logger.warning(f"Cannot reach Elasticsearch for dataset {dataset.name}: {e}")
            raise ElasticServiceError(f"Cannot reach Elasticsearch at {dataset.url}", 503)
        except AuthenticationException:
            raise ElasticServiceError("Elasticsearch authentication failed, check the credentials", 502)
        except AuthorizationException as e:
            raise ElasticServiceError(f"Elasticsearch refused the action: {_error_reason(e)}", 502)
        except NotFoundError as e:
            raise ElasticServiceError(f"Not found: {_error_reason(e)}", 404)
        except ConflictError as e:
            raise ElasticServiceError(_error_reason(e), 409)
        except BadRequestError as e:
            if (isinstance(e.body, dict) and isinstance(e.body.get('error'), dict)
                    and e.body['error'].get('type') == 'resource_already_exists_exception'):
                raise ElasticServiceError(_error_reason(e), 409)
            raise ElasticServiceError(f"Invalid Elasticsearch request: {_error_reason(e)}", 400)
        except ApiError as e:
            raise ElasticServiceError(f"Elasticsearch error: {_error_reason(e)}", 502)
        finally:
            client.close()

    # ------------------------------------------------------------------
    # Cluster and indices
    # ------------------------------------------------------------------

    def info(self, dataset: ElasticDataset) -> Dict[str, Any]:
        with self.connect(dataset) as client:
            info = client.info()
            result = {
                "clusterName": info.get("cluster_name"),
                "version": info.get("version", {}).get("number"),
                "status": None,
                "numberOfNodes": None,
                "activeShards": None,
                "unassignedShards": None,
            }
            try:
                health = client.cluster.health()
                result.update({
                    "status": health.get("status"),
                    "numberOfNodes": health.get("number_of_nodes"),
                    "activeShards": health.get("active_shards"),
                    "unassignedShards": health.get("unassigned_shards"),
                })
            except AuthorizationException:
                # cluster health requires the 'monitor' cluster privilege
                pass
            return result

    def list_indices(self, dataset: ElasticDataset, include_hidden: bool = False) -> List[Dict[str, Any]]:
        with self.connect(dataset) as client:
            rows = client.cat.indices(
                format="json",
                h="index,health,status,docs.count,store.size,pri,rep",
                s="index",
                bytes="b",
                expand_wildcards="all" if include_hidden else "open",
            )
            aliases: Dict[str, List[str]] = {}
            try:
                for alias in client.cat.aliases(format="json", h="alias,index"):
                    aliases.setdefault(alias["index"], []).append(alias["alias"])
            except AuthorizationException:
                pass

        indices = []
        for row in rows:
            name = row.get("index")
            if not include_hidden and name.startswith('.'):
                continue
            indices.append({
                "index": name,
                "health": row.get("health"),
                "status": row.get("status"),
                "docsCount": int(row["docs.count"]) if row.get("docs.count") else None,
                "sizeBytes": int(row["store.size"]) if row.get("store.size") else None,
                "primaries": int(row["pri"]) if row.get("pri") else None,
                "replicas": int(row["rep"]) if row.get("rep") else None,
                "aliases": sorted(aliases.get(name, [])),
            })
        return indices

    def index_names(self, dataset: ElasticDataset) -> List[str]:
        return [i["index"] for i in self.list_indices(dataset)]

    def index_exists(self, dataset: ElasticDataset, index: str) -> bool:
        with self.connect(dataset) as client:
            return bool(client.indices.exists(index=index))

    def get_mapping(self, dataset: ElasticDataset, index: str) -> Dict[str, Any]:
        with self.connect(dataset) as client:
            resp = client.indices.get_mapping(index=index)
        # The response is keyed by concrete index name (an alias may point to several)
        return next(iter(resp.values()), {}).get("mappings", {})

    def create_index(self, dataset: ElasticDataset, index: str,
                     mappings: Optional[Dict[str, Any]] = None,
                     settings: Optional[Dict[str, Any]] = None) -> None:
        if not index:
            raise ElasticServiceError("The index name is required", 400)
        try:
            _validate_es_index(index)
        except ValueError as e:
            raise ElasticServiceError(str(e), 400)
        with self.connect(dataset) as client:
            client.indices.create(index=index, mappings=mappings or None, settings=settings or None)

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def search_page(self, dataset: ElasticDataset, index: str, page: int = 1, per_page: int = 10,
                    query: Any = None, include_id: bool = True,
                    fields: Optional[List[str]] = None) -> Tuple[List[dict], int]:
        """Return one page of documents and the total number of matching documents."""
        page = max(page or 1, 1)
        per_page = max(per_page or 10, 1)
        kwargs: Dict[str, Any] = {
            "index": index,
            "query": parse_query(query),
            "from_": (page - 1) * per_page,
            "size": per_page,
            "track_total_hits": True,
        }
        if fields:
            kwargs["source"] = fields
        with self.connect(dataset) as client:
            resp = client.search(**kwargs)
        total = resp["hits"]["total"]["value"]
        return hits_to_records(resp["hits"]["hits"], include_id), total

    def count(self, dataset: ElasticDataset, index: str, query: Any = None) -> int:
        with self.connect(dataset) as client:
            return client.count(index=index, query=parse_query(query))["count"]

    def scan(self, dataset: ElasticDataset, index: str, query: Any = None,
             fields: Optional[List[str]] = None, max_docs: Optional[int] = None,
             batch_size: int = SCAN_BATCH_SIZE) -> Iterator[List[dict]]:
        """Yield every matching hit in batches, using a point in time and search_after.

        Unlike from/size, this is not limited by index.max_result_window (10,000 by default).
        """
        es_query = parse_query(query)
        with self.connect(dataset) as client:
            pit_id = client.open_point_in_time(index=index, keep_alive=PIT_KEEP_ALIVE)["id"]
            try:
                fetched = 0
                search_after = None
                while max_docs is None or fetched < max_docs:
                    size = batch_size if max_docs is None else min(batch_size, max_docs - fetched)
                    kwargs: Dict[str, Any] = {
                        "pit": {"id": pit_id, "keep_alive": PIT_KEEP_ALIVE},
                        "sort": [{"_shard_doc": "asc"}],
                        "size": size,
                        "query": es_query,
                        "track_total_hits": False,
                    }
                    if fields:
                        kwargs["source"] = fields
                    if search_after is not None:
                        kwargs["search_after"] = search_after
                    resp = client.search(**kwargs)
                    pit_id = resp.get("pit_id", pit_id)
                    hits = resp["hits"]["hits"]
                    if not hits:
                        break
                    yield hits
                    fetched += len(hits)
                    search_after = hits[-1]["sort"]
            finally:
                try:
                    client.close_point_in_time(id=pit_id)
                except ApiError:
                    logger.debug("Could not close point in time", exc_info=True)

    def read_dataframe(self, dataset: ElasticDataset, index: str, query: Any = None,
                       fields: Optional[List[str]] = None, max_docs: Optional[int] = None,
                       include_id: bool = True) -> pd.DataFrame:
        records: List[dict] = []
        for hits in self.scan(dataset, index, query=query, fields=fields, max_docs=max_docs):
            records.extend(hits_to_records(hits, include_id))
        return pd.DataFrame(records)

    def sample_dataframe(self, dataset: ElasticDataset, index: str, size: int = 20, query: Any = None,
                         fields: Optional[List[str]] = None, include_id: bool = True) -> pd.DataFrame:
        with self.connect(dataset) as client:
            kwargs: Dict[str, Any] = {"index": index, "query": parse_query(query), "size": size}
            if fields:
                kwargs["source"] = fields
            resp = client.search(**kwargs)
        return pd.DataFrame(hits_to_records(resp["hits"]["hits"], include_id))

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def bulk_index(self, client: Elasticsearch, index: str, records: Iterable[dict],
                   id_field: Optional[str] = None) -> Tuple[int, int, List[str]]:
        """Index records with the bulk API, on a client opened with connect().

        The '_id' key is never sent in the document body (it is an Elasticsearch metadata
        field); it is used as the document id only when id_field is '_id'.

        Returns:
            (indexed count, failed count, first error messages)
        """
        def actions():
            for record in records:
                source = {k: to_json_safe(v) for k, v in record.items() if k != '_id'}
                action: Dict[str, Any] = {"_index": index, "_source": source}
                doc_id = record.get(id_field) if id_field else None
                if doc_id is not None and not (isinstance(doc_id, float) and math.isnan(doc_id)):
                    action["_id"] = str(to_json_safe(doc_id))
                yield action

        indexed, failed, errors = 0, 0, []
        for ok, item in helpers.streaming_bulk(client, actions(), chunk_size=BULK_CHUNK_SIZE,
                                               raise_on_error=False):
            if ok:
                indexed += 1
                continue
            failed += 1
            if len(errors) < MAX_REPORTED_BULK_ERRORS:
                error = next(iter(item.values()), {}).get("error", item)
                errors.append(error.get("reason", str(error)) if isinstance(error, dict) else str(error))
        return indexed, failed, errors
