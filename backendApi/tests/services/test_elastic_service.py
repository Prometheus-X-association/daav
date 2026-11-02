"""
Unit tests for ElasticService (Elasticsearch client mocked).
"""
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from elastic_transport import ApiResponseMeta, HttpHeaders, NodeConfig
from elasticsearch import (
    AuthenticationException,
    AuthorizationException,
    BadRequestError,
    ConnectionError as EsConnectionError,
    NotFoundError,
)

from app.models.interface.dataset_interface import ElasticDataset
from app.services import elastic_service
from app.services.elastic_service import (
    ElasticService,
    ElasticServiceError,
    hits_to_records,
    infer_mappings,
    parse_query,
    to_json_safe,
)


def make_dataset(**kwargs):
    defaults = dict(type="elastic", name="es", url="https://es.example.com:9200", verifyCerts=True)
    defaults.update(kwargs)
    return ElasticDataset.model_construct(**defaults)


def api_error(cls, status, body):
    meta = ApiResponseMeta(status=status, http_version="1.1", headers=HttpHeaders(), duration=0.0,
                           node=NodeConfig("https", "es.example.com", 9200))
    return cls("error", meta, body)


@pytest.fixture
def client():
    """Patch the Elasticsearch class and the DNS check; return the client instance."""
    with patch.object(elastic_service, "Elasticsearch") as es_cls, \
            patch.object(elastic_service, "ensure_public_url"):
        instance = MagicMock()
        es_cls.return_value = instance
        instance.es_cls = es_cls
        yield instance


# ===========================
# HELPERS
# ===========================

class TestParseQuery:

    @pytest.mark.parametrize("query", [None, "", "   "])
    def test_empty_matches_all(self, query):
        assert parse_query(query) == {"match_all": {}}

    def test_plain_text_is_query_string(self):
        assert parse_query("category:books AND price:>20") == {
            "query_string": {"query": "category:books AND price:>20"}
        }

    def test_json_clause(self):
        assert parse_query('{"term": {"category": "books"}}') == {"term": {"category": "books"}}

    def test_json_wrapped_in_query(self):
        assert parse_query('{"query": {"match": {"name": "x"}}}') == {"match": {"name": "x"}}

    def test_dict_accepted(self):
        assert parse_query({"match_all": {}}) == {"match_all": {}}

    def test_invalid_json_rejected(self):
        with pytest.raises(ElasticServiceError) as exc:
            parse_query("{bad json")
        assert exc.value.status_code == 400

    @pytest.mark.parametrize("query", ['{}', '{"match": {}, "term": {}}', '{"query": {}, "size": 10}'])
    def test_not_a_single_clause_rejected(self, query):
        with pytest.raises(ElasticServiceError):
            parse_query(query)


class TestConversions:

    def test_hits_to_records_with_and_without_id(self):
        hits = [{"_id": "1", "_source": {"a": 1}}, {"_id": "2"}]
        assert hits_to_records(hits) == [{"_id": "1", "a": 1}, {"_id": "2"}]
        assert hits_to_records(hits, include_id=False) == [{"a": 1}, {}]

    def test_to_json_safe(self):
        value = {
            "nan": float("nan"),
            "nat": pd.NaT,
            "ts": pd.Timestamp("2025-01-02T03:04:05"),
            "int": np.int64(3),
            "bool": np.bool_(True),
            "arr": np.array([1, 2]),
            "nested": {"f": np.float64(1.5), "l": [np.nan]},
        }
        assert to_json_safe(value) == {
            "nan": None,
            "nat": None,
            "ts": "2025-01-02T03:04:05",
            "int": 3,
            "bool": True,
            "arr": [1, 2],
            "nested": {"f": 1.5, "l": [None]},
        }

    def test_infer_mappings(self):
        df = pd.DataFrame({
            "_id": ["a"], "i": [1], "f": [1.5], "b": [True],
            "d": pd.to_datetime(["2025-01-01"]), "s": ["x"], "o": [{"k": 1}],
        })
        assert infer_mappings(df) == {"properties": {
            "i": {"type": "long"}, "f": {"type": "double"}, "b": {"type": "boolean"}, "d": {"type": "date"},
        }}


# ===========================
# CONNECTION
# ===========================

class TestConnect:

    @pytest.mark.parametrize("kwargs, expected", [
        (dict(key="k", user="u", password="p", bearerToken="t"), {"api_key": "k"}),
        (dict(user="u", password="p", bearerToken="t"), {"basic_auth": ("u", "p")}),
        (dict(bearerToken="t"), {"bearer_auth": "t"}),
        (dict(user="u"), {}),
    ])
    def test_auth_priority(self, client, kwargs, expected):
        with ElasticService().connect(make_dataset(**kwargs)):
            pass
        call_kwargs = client.es_cls.call_args.kwargs
        for auth in ("api_key", "basic_auth", "bearer_auth"):
            assert call_kwargs.get(auth) == expected.get(auth)
        client.close.assert_called_once()

    @pytest.mark.parametrize("kwargs, expected", [
        (dict(authMode="basic", key="stale", user="u", password="p"), {"basic_auth": ("u", "p")}),
        (dict(authMode="apiKey", key="k", user="u", password="p"), {"api_key": "k"}),
        (dict(authMode="bearer", key="stale", bearerToken="t"), {"bearer_auth": "t"}),
        (dict(authMode="none", key="stale", user="u", password="p"), {}),
    ])
    def test_explicit_auth_mode(self, client, kwargs, expected):
        with ElasticService().connect(make_dataset(**kwargs)):
            pass
        call_kwargs = client.es_cls.call_args.kwargs
        for auth in ("api_key", "basic_auth", "bearer_auth"):
            assert call_kwargs.get(auth) == expected.get(auth)

    @pytest.mark.parametrize("kwargs", [
        dict(authMode="basic", user="u"),
        dict(authMode="apiKey"),
        dict(authMode="bearer"),
    ])
    def test_missing_credentials_for_auth_mode(self, client, kwargs):
        with pytest.raises(ElasticServiceError) as exc:
            with ElasticService().connect(make_dataset(**kwargs)):
                pass
        assert exc.value.status_code == 400
        client.es_cls.assert_not_called()

    def test_empty_auth_mode_is_none(self):
        assert ElasticDataset.empty_auth_mode("") is None

    def test_verify_certs_option(self, client):
        with ElasticService().connect(make_dataset(verifyCerts=False)):
            pass
        assert client.es_cls.call_args.kwargs["verify_certs"] is False

    def test_missing_url(self, client):
        with pytest.raises(ElasticServiceError) as exc:
            with ElasticService().connect(make_dataset(url=None)):
                pass
        assert exc.value.status_code == 400

    def test_ssrf_refused_before_connecting(self):
        with patch.object(elastic_service, "Elasticsearch") as es_cls:
            with pytest.raises(ElasticServiceError) as exc:
                ElasticService().info(make_dataset(url="http://169.254.169.254"))
        assert exc.value.status_code == 400
        es_cls.assert_not_called()

    @pytest.mark.parametrize("error, status", [
        (EsConnectionError("refused"), 503),
        (api_error(AuthenticationException, 401, {}), 502),
        (api_error(AuthorizationException, 403, {"error": {"reason": "denied"}}), 502),
        (api_error(NotFoundError, 404, {"error": {"root_cause": [{"reason": "no such index"}]}}), 404),
        (api_error(BadRequestError, 400, {"error": {"type": "parsing_exception", "reason": "bad"}}), 400),
        (api_error(BadRequestError, 400, {"error": {"type": "resource_already_exists_exception", "reason": "exists"}}), 409),
    ])
    def test_errors_are_translated(self, client, error, status):
        client.info.side_effect = error
        with pytest.raises(ElasticServiceError) as exc:
            ElasticService().info(make_dataset())
        assert exc.value.status_code == status
        client.close.assert_called_once()

    def test_authorization_reason_reported(self, client):
        client.count.side_effect = api_error(AuthorizationException, 403, {"error": {"reason": "missing read"}})
        with pytest.raises(ElasticServiceError, match="missing read"):
            ElasticService().count(make_dataset(), "idx")


# ===========================
# CLUSTER AND INDICES
# ===========================

class TestIndices:

    def test_info_without_monitor_privilege(self, client):
        client.info.return_value = {"cluster_name": "c", "version": {"number": "8.15.5"}}
        client.cluster.health.side_effect = api_error(AuthorizationException, 403, {})
        info = ElasticService().info(make_dataset())
        assert info["clusterName"] == "c" and info["version"] == "8.15.5" and info["status"] is None

    def test_list_indices(self, client):
        client.cat.indices.return_value = [
            {"index": ".kibana", "health": "green", "status": "open", "docs.count": "1", "store.size": "10", "pri": "1", "rep": "0"},
            {"index": "products", "health": "green", "status": "open", "docs.count": "50", "store.size": "1024", "pri": "1", "rep": "0"},
            {"index": "closed", "health": None, "status": "close", "docs.count": None, "store.size": None, "pri": "1", "rep": "1"},
        ]
        client.cat.aliases.return_value = [{"alias": "shop", "index": "products"}]
        indices = ElasticService().list_indices(make_dataset())
        assert [i["index"] for i in indices] == ["products", "closed"]
        assert indices[0] == {"index": "products", "health": "green", "status": "open", "docsCount": 50,
                              "sizeBytes": 1024, "primaries": 1, "replicas": 0, "aliases": ["shop"]}
        assert indices[1]["docsCount"] is None
        assert client.cat.indices.call_args.kwargs["expand_wildcards"] == "open"

    def test_list_hidden_indices(self, client):
        client.cat.indices.return_value = [{"index": ".kibana"}]
        client.cat.aliases.return_value = []
        indices = ElasticService().list_indices(make_dataset(), include_hidden=True)
        assert [i["index"] for i in indices] == [".kibana"]
        assert client.cat.indices.call_args.kwargs["expand_wildcards"] == "all"

    def test_get_mapping_of_alias(self, client):
        client.indices.get_mapping.return_value = {"products-v2": {"mappings": {"properties": {"a": {}}}}}
        assert ElasticService().get_mapping(make_dataset(), "products") == {"properties": {"a": {}}}

    @pytest.mark.parametrize("name", ["", "UPPER", "*", "a b"])
    def test_create_index_invalid_name(self, client, name):
        with pytest.raises(ElasticServiceError) as exc:
            ElasticService().create_index(make_dataset(), name)
        assert exc.value.status_code == 400
        client.indices.create.assert_not_called()

    def test_create_index(self, client):
        ElasticService().create_index(make_dataset(), "new-index", mappings={"properties": {}})
        client.indices.create.assert_called_once_with(index="new-index", mappings={"properties": {}}, settings=None)


# ===========================
# READING
# ===========================

class TestReading:

    def test_search_page(self, client):
        client.search.return_value = {"hits": {"total": {"value": 42}, "hits": [{"_id": "11", "_source": {"a": 1}}]}}
        data, total = ElasticService().search_page(make_dataset(), "idx", page=2, per_page=10, query="a:1")
        assert data == [{"_id": "11", "a": 1}] and total == 42
        kwargs = client.search.call_args.kwargs
        assert kwargs["from_"] == 10 and kwargs["size"] == 10
        assert kwargs["query"] == {"query_string": {"query": "a:1"}}

    def _pages(self, client, pages):
        client.open_point_in_time.return_value = {"id": "pit-1"}
        client.search.side_effect = [
            {"pit_id": "pit-2", "hits": {"hits": [{"_id": str(i), "_source": {"n": i}, "sort": [i]} for i in page]}}
            for page in pages
        ]

    def test_scan_uses_search_after_and_closes_pit(self, client):
        self._pages(client, [[1, 2], [3], []])
        batches = list(ElasticService().scan(make_dataset(), "idx", batch_size=2))
        assert [len(b) for b in batches] == [2, 1]
        calls = client.search.call_args_list
        assert "search_after" not in calls[0].kwargs
        assert calls[1].kwargs["search_after"] == [2]
        assert calls[1].kwargs["pit"]["id"] == "pit-2"
        client.close_point_in_time.assert_called_once_with(id="pit-2")

    def test_scan_respects_max_docs(self, client):
        self._pages(client, [[1, 2], [3]])
        batches = list(ElasticService().scan(make_dataset(), "idx", batch_size=2, max_docs=3))
        assert sum(len(b) for b in batches) == 3
        assert client.search.call_args_list[1].kwargs["size"] == 1

    def test_scan_closes_pit_on_error(self, client):
        client.open_point_in_time.return_value = {"id": "pit-1"}
        client.search.side_effect = api_error(BadRequestError, 400, {"error": {"reason": "bad"}})
        with pytest.raises(ElasticServiceError):
            list(ElasticService().scan(make_dataset(), "idx"))
        client.close_point_in_time.assert_called_once_with(id="pit-1")

    def test_read_dataframe(self, client):
        self._pages(client, [[1, 2], []])
        df = ElasticService().read_dataframe(make_dataset(), "idx", fields=["n"], include_id=False)
        assert list(df.columns) == ["n"] and df["n"].tolist() == [1, 2]
        assert client.search.call_args_list[0].kwargs["source"] == ["n"]


# ===========================
# WRITING
# ===========================

class TestBulkIndex:

    def _run(self, records, id_field=None, results=None):
        sent = []

        def fake_bulk(client, actions, **kwargs):
            for action in actions:
                sent.append(action)
            return iter(results if results is not None else [(True, {})] * len(sent))

        with patch.object(elastic_service.helpers, "streaming_bulk", side_effect=fake_bulk):
            outcome = ElasticService().bulk_index(MagicMock(), "idx", records, id_field=id_field)
        return sent, outcome

    def test_id_never_in_source(self):
        sent, (indexed, failed, errors) = self._run([{"_id": "a", "x": 1}])
        assert sent == [{"_index": "idx", "_source": {"x": 1}}]
        assert (indexed, failed, errors) == (1, 0, [])

    def test_id_field(self):
        sent, _ = self._run([{"_id": "a", "x": 1}, {"_id": None, "x": 2}], id_field="_id")
        assert sent[0]["_id"] == "a" and "_id" not in sent[1]
        sent, _ = self._run([{"sku": np.int64(7), "x": 1}], id_field="sku")
        assert sent[0]["_id"] == "7" and sent[0]["_source"] == {"sku": 7, "x": 1}

    def test_values_cleaned(self):
        sent, _ = self._run([{"x": float("nan"), "d": pd.Timestamp("2025-01-01")}])
        assert sent[0]["_source"] == {"x": None, "d": "2025-01-01T00:00:00"}

    def test_failures_reported(self):
        results = [(True, {}), (False, {"index": {"error": {"reason": "mapper_parsing_exception"}}})]
        _, (indexed, failed, errors) = self._run([{"x": 1}, {"x": "y"}], results=results)
        assert (indexed, failed) == (1, 1)
        assert errors == ["mapper_parsing_exception"]
