"""
Security tests for injection validators in dataset_interface models.
Covers: SQL injection (MySQL), Elasticsearch wildcard, SSRF (API/Elastic URLs).
"""
import pytest
from pydantic import ValidationError

from app.models.interface.dataset_interface import (
    MysqlDataset,
    ElasticDataset,
    ApiDataset,
    DatasetParams,
)


# ---------------------------------------------------------------------------
# MysqlDataset – SQL injection via identifiants (database / table)
# ---------------------------------------------------------------------------

class TestMysqlDatasetSqlInjection:

    def test_valid_database_name(self):
        ds = MysqlDataset(type="mysql", database="my_database")
        assert ds.database == "my_database"

    def test_valid_table_name(self):
        ds = MysqlDataset(type="mysql", table="user_data_2024")
        assert ds.table == "user_data_2024"

    def test_none_database_is_allowed(self):
        ds = MysqlDataset(type="mysql", database=None)
        assert ds.database is None

    def test_none_table_is_allowed(self):
        ds = MysqlDataset(type="mysql", table=None)
        assert ds.table is None

    @pytest.mark.parametrize("payload", [
        "users; DROP TABLE users --",
        "db' OR '1'='1",
        "db`injection`",
        "test--comment",
        "db; SELECT * FROM secrets",
        "db UNION SELECT password FROM users",
        "../etc/passwd",
        "db\x00null",
    ])
    def test_sql_injection_in_database_is_rejected(self, payload):
        with pytest.raises(ValidationError) as exc_info:
            MysqlDataset(type="mysql", database=payload)
        assert "database" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    @pytest.mark.parametrize("payload", [
        "users; DROP TABLE users --",
        "table' OR '1'='1",
        "table`evil`",
        "1337; DELETE FROM secrets",
        "t UNION SELECT * FROM passwords",
    ])
    def test_sql_injection_in_table_is_rejected(self, payload):
        with pytest.raises(ValidationError) as exc_info:
            MysqlDataset(type="mysql", table=payload)
        assert "table" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_identifier_too_long_is_rejected(self):
        with pytest.raises(ValidationError):
            MysqlDataset(type="mysql", database="a" * 65)


# ---------------------------------------------------------------------------
# DatasetParams – même protection que MysqlDataset (utilisée dans les queries)
# ---------------------------------------------------------------------------

class TestDatasetParamsSqlInjection:

    def test_valid_params(self):
        params = DatasetParams(database="my_db", table="my_table")
        assert params.database == "my_db"
        assert params.table == "my_table"

    @pytest.mark.parametrize("payload", [
        "db'; DROP DATABASE mydb --",
        "tbl`; SELECT 1",
        "a b",          # espace
        "db-name",      # tiret (non autorisé dans les identifiants MySQL)
        "db.name",      # point
    ])
    def test_injection_in_database_is_rejected(self, payload):
        with pytest.raises(ValidationError):
            DatasetParams(database=payload)

    @pytest.mark.parametrize("payload", [
        "table'; DELETE FROM users --",
        "t UNION SELECT secret FROM creds",
    ])
    def test_injection_in_table_is_rejected(self, payload):
        with pytest.raises(ValidationError):
            DatasetParams(table=payload)


# ---------------------------------------------------------------------------
# ElasticDataset – wildcard d'index
# ---------------------------------------------------------------------------

class TestElasticDatasetIndexValidation:

    def test_valid_index_name(self):
        ds = ElasticDataset(type="elastic", index="my_index-2024.01.01")
        assert ds.index == "my_index-2024.01.01"

    def test_none_index_is_allowed(self):
        ds = ElasticDataset(type="elastic", index=None)
        assert ds.index is None

    @pytest.mark.parametrize("wildcard", ["*", "_all", ".*"])
    def test_wildcard_index_is_rejected(self, wildcard):
        with pytest.raises(ValidationError) as exc_info:
            ElasticDataset(type="elastic", index=wildcard)
        assert "wildcard" in str(exc_info.value).lower() or "index" in str(exc_info.value).lower()

    @pytest.mark.parametrize("payload", [
        "MY_INDEX",          # majuscules interdites en ES
        "index with space",
        "index;DROP",
        "index<script>",
    ])
    def test_invalid_index_name_is_rejected(self, payload):
        with pytest.raises(ValidationError):
            ElasticDataset(type="elastic", index=payload)


# ---------------------------------------------------------------------------
# ElasticDataset / ApiDataset – SSRF via URL
# ---------------------------------------------------------------------------

class TestSsrfUrlValidation:

    @pytest.mark.parametrize("safe_url", [
        "https://my-elasticsearch.example.com:9200",
        "http://public-api.example.com/data",
        "https://api.github.com/repos",
    ])
    def test_valid_external_url_accepted(self, safe_url):
        ds = ElasticDataset(type="elastic", url=safe_url)
        assert ds.url == safe_url

    @pytest.mark.parametrize("ssrf_url", [
        "http://localhost:9200",
        "http://127.0.0.1/admin",
        "http://0.0.0.0/secret",
        "http://10.0.0.1/internal",
        "http://172.16.0.1/metadata",
        "http://192.168.1.1/router",
        "http://169.254.169.254/latest/meta-data/",  # AWS metadata
    ])
    def test_ssrf_url_is_rejected_for_elastic(self, ssrf_url):
        with pytest.raises(ValidationError) as exc_info:
            ElasticDataset(type="elastic", url=ssrf_url)
        errors = str(exc_info.value).lower()
        assert any(word in errors for word in ("private", "internal", "localhost", "scheme", "url"))

    @pytest.mark.parametrize("ssrf_url", [
        "http://localhost/api",
        "http://127.0.0.1:8080",
        "http://10.10.10.10/data",
        "http://192.168.0.1/admin",
        "http://169.254.169.254/latest/meta-data/",
    ])
    def test_ssrf_url_is_rejected_for_api(self, ssrf_url):
        with pytest.raises(ValidationError) as exc_info:
            ApiDataset(type="api", url=ssrf_url)
        errors = str(exc_info.value).lower()
        assert any(word in errors for word in ("private", "internal", "localhost", "scheme", "url"))

    @pytest.mark.parametrize("ssrf_url", [
        "http://localhost/oauth/token",
        "http://169.254.169.254/iam/token",
    ])
    def test_ssrf_auth_url_is_rejected(self, ssrf_url):
        with pytest.raises(ValidationError):
            ApiDataset(type="api", authUrl=ssrf_url)

    def test_non_http_scheme_rejected_for_elastic(self):
        with pytest.raises(ValidationError):
            ElasticDataset(type="elastic", url="ftp://example.com/data")

    def test_non_http_scheme_rejected_for_api(self):
        with pytest.raises(ValidationError):
            ApiDataset(type="api", url="file:///etc/passwd")

    def test_none_url_is_allowed(self):
        ds = ApiDataset(type="api", url=None)
        assert ds.url is None
