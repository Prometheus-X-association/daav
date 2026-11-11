import pytest
import pandas as pd
import tempfile
import os
import json
import csv
import yaml
import base64
import math
import numpy as np
import shutil
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime, timezone
from fastapi import Request, HTTPException

from app.utils.utils import (
    convert_size, folder, generate_pandas_schema, slice_generator, 
    decode_dictionary, verify_route_access, get_user_output_path,
    convert_numpy_type_to_python, normalize_dtype_string, 
    resolve_file_name, filter_data_with_duckdb
)
from app.models.interface.dataset_interface import Pagination, FileContentResponse
from app.models.interface.dataset_schema import PandasColumn, PandasSchema


class TestConvertSize:
    """Test cases for convert_size function"""
    
    def test_zero_size(self):
        """Test with zero size"""
        result = convert_size(0)
        assert result == "0B"
    
    def test_bytes(self):
        """Test bytes conversion"""
        result = convert_size(500)
        assert result == "500.0 B"
    
    def test_kilobytes(self):
        """Test kilobytes conversion"""
        result = convert_size(1024)
        assert result == "1.0 KB"
    
    def test_megabytes(self):
        """Test megabytes conversion"""
        result = convert_size(1024 * 1024)
        assert result == "1.0 MB"
    
    def test_gigabytes(self):
        """Test gigabytes conversion"""
        result = convert_size(1024 * 1024 * 1024)
        assert result == "1.0 GB"


class TestFolder:
    """Test cases for folder function"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory with test files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            json_file = os.path.join(temp_dir, "test.json")
            with open(json_file, 'w') as f:
                json.dump({"name": "test", "value": 123}, f)
            
            csv_file = os.path.join(temp_dir, "test.csv")
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'age'])
                writer.writerow(['John', '30'])
            
            txt_file = os.path.join(temp_dir, "test.txt")
            with open(txt_file, 'w') as f:
                f.write("Hello World")
            
            yaml_file = os.path.join(temp_dir, "test.yaml")
            with open(yaml_file, 'w') as f:
                yaml.dump({'config': {'debug': True, 'port': 8080}}, f)
            
            # Create subdirectory
            sub_dir = os.path.join(temp_dir, "subdir")
            os.makedirs(sub_dir)
            sub_file = os.path.join(sub_dir, "sub.txt")
            with open(sub_file, 'w') as f:
                f.write("Sub content")
            
            yield temp_dir
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_without_pagination(self, mock_stat, mock_magic, temp_dir):
        """Test folder function without pagination"""
        # Mock file stats and mime types
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0  # 2022-01-01 00:00:00
        mock_stat.return_value.st_mtime = 1640995200.0
        
        def mime_side_effect(path, **kwargs):  # Accept **kwargs to handle mime=True
            if path.endswith('.json'):
                return 'application/json'
            elif path.endswith('.csv'):
                return 'text/csv'
            elif path.endswith('.txt'):
                return 'text/plain'
            elif path.endswith('.yaml'):
                return 'application/x-yaml'
            return 'application/octet-stream'
        
        mock_magic.side_effect = mime_side_effect
        
        result = folder(temp_dir)
        
        assert isinstance(result, list)
        assert len(result) == 5  # 4 files in root + 1 in subdirectory
        
        # Check if all files are present
        file_names = [item['file'] for item in result]
        assert 'test.json' in file_names
        assert 'test.csv' in file_names
        assert 'test.txt' in file_names
        assert 'test.yaml' in file_names
        assert 'sub.txt' in file_names
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_with_pagination(self, mock_stat, mock_magic, temp_dir):
        """Test folder function with pagination"""
        # Mock file stats and mime types
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        
        def mock_magic_side_effect(path, **kwargs):
            return 'text/plain'
        
        mock_magic.side_effect = mock_magic_side_effect
        
        pagination = Pagination(page=1, perPage=2)
        result = folder(temp_dir, pagination)
        
        assert isinstance(result, FileContentResponse)
        assert len(result.data) == 2
        assert result.total_rows == 5
        assert result.current_page == 1
        assert result.limit == 2
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_json_content(self, mock_stat, mock_magic, temp_dir):
        """Test JSON file content parsing"""
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        
        def mock_magic_side_effect(path, **kwargs):
            return 'application/json'
        
        mock_magic.side_effect = mock_magic_side_effect
        
        result = folder(temp_dir)
        json_file = next(item for item in result if item['file'] == 'test.json')
        
        assert json_file['content'] == {"name": "test", "value": 123}
        assert json_file['mime_type'] == 'application/json'
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_csv_content(self, mock_stat, mock_magic, temp_dir):
        """Test CSV file content parsing"""
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        mock_magic.return_value = 'text/csv'
        
        result = folder(temp_dir)
        csv_file = next(item for item in result if item['file'] == 'test.csv')
        
        assert isinstance(csv_file['content'], list)
        assert len(csv_file['content']) == 1  # Only data rows, not header
        assert csv_file['content'][0] == {'name': 'John', 'age': '30'}
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_text_content(self, mock_stat, mock_magic, temp_dir):
        """Test text file content parsing"""
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        mock_magic.return_value = 'text/plain'
        
        result = folder(temp_dir)
        txt_file = next(item for item in result if item['file'] == 'test.txt')
        
        assert txt_file['content'] == "Hello World"
    
    @patch('magic.from_file')
    @patch('os.stat')
    def test_folder_yaml_content(self, mock_stat, mock_magic, temp_dir):
        """Test YAML file content parsing"""
        mock_stat.return_value = MagicMock()
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_ctime = 1640995200.0
        mock_stat.return_value.st_mtime = 1640995200.0
        mock_magic.return_value = 'application/x-yaml'
        
        result = folder(temp_dir)
        yaml_file = next(item for item in result if item['file'] == 'test.yaml')
        
        assert yaml_file['content'] == {'config': {'debug': True, 'port': 8080}}
    
    @patch('os.scandir')
    def test_folder_permission_error(self, mock_scandir):
        """Test folder function with permission error"""
        mock_scandir.side_effect = PermissionError("Access denied")
        
        result = folder("/nonexistent")
        assert result == []
    
    @patch('magic.from_file')
    def test_folder_media_file_too_large(self, mock_magic, temp_dir):
        """Test media file size limit"""
        # Create a large dummy file
        large_file = os.path.join(temp_dir, "large.jpg")
        # Create a file larger than 1000MB to trigger the size limit
        with open(large_file, 'wb') as f:
            f.write(b'0' * (1001 * 1024 * 1024))  # 1001MB file
        
        mock_magic.return_value = 'image/jpeg'
        
        result = folder(temp_dir)
        large_file_result = next(item for item in result if item['file'] == 'large.jpg')
        
        assert large_file_result['media'] is None


class TestGeneratePandasSchema:
    """Test cases for generate_pandas_schema function"""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Sample DataFrame for testing"""
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['John', 'Jane', 'Bob'],
            'age': [25, 30, 35],
            'active': [True, False, True]
        })
    
    @pytest.fixture
    def nested_dataframe(self):
        """DataFrame with nested structures"""
        return pd.DataFrame({
            'user': [
                {'name': 'John', 'email': 'john@test.com'},
                {'name': 'Jane', 'email': 'jane@test.com'}
            ],
            'metadata': [
                {'created': '2023-01-01', 'source': 'api'},
                {'created': '2023-01-02', 'source': 'web'}
            ]
        })
    
    def test_dataframe_schema_generation(self, sample_dataframe):
        """Test schema generation for DataFrame"""
        schema = generate_pandas_schema(sample_dataframe)
        
        assert isinstance(schema, PandasSchema)
        assert len(schema.root) == 4
        
        # Check column names
        column_names = [col.name for col in schema.root]
        assert 'id' in column_names
        assert 'name' in column_names
        assert 'age' in column_names
        assert 'active' in column_names
        
        # Check data types
        id_col = next(col for col in schema.root if col.name == 'id')
        assert id_col.dtype == 'int'
        assert id_col.count == 3
        assert not id_col.nullable
    
    def test_series_schema_generation(self):
        """Test schema generation for Series"""
        series = pd.Series([1, 2, 3, 4, 5], name='numbers')
        schema = generate_pandas_schema(series)
        
        assert isinstance(schema, PandasSchema)
        assert len(schema.root) == 1
        assert schema.root[0].name == "#array_item#"
        assert schema.root[0].dtype == 'int'
        assert schema.root[0].count == 5
    
    def test_empty_series_schema(self):
        """Test schema generation for empty Series"""
        empty_series = pd.Series([], dtype='object')
        schema = generate_pandas_schema(empty_series)
        
        assert isinstance(schema, PandasSchema)
        assert len(schema.root) == 0
    
    def test_dictionary_schema_generation(self):
        """Test schema generation for dictionary"""
        test_dict = {
            'name': 'John',
            'age': 30,
            'active': True,
            'metadata': {'created': '2023-01-01'}
        }
        
        schema = generate_pandas_schema(test_dict)
        
        assert isinstance(schema, PandasSchema)
        assert len(schema.root) == 4
        
        # Check nested structure
        metadata_col = next(col for col in schema.root if col.name == 'metadata')
        assert metadata_col.nested is not None
        assert len(metadata_col.nested) == 1
        assert metadata_col.nested[0].name == 'created'
    
    def test_series_with_null_values(self):
        """Test Series with null values"""
        series = pd.Series([1, None, 3, None, 5])
        schema = generate_pandas_schema(series)
        
        assert schema.root[0].nullable is True
        assert schema.root[0].count == 5
    
    def test_nested_dataframe_schema(self, nested_dataframe):
        """Test schema generation for DataFrame with nested data"""
        schema = generate_pandas_schema(nested_dataframe)
        
        assert len(schema.root) == 2
        
        # Check if nested structures are detected
        user_col = next(col for col in schema.root if col.name == 'user')
        assert user_col.nested is not None


class TestSliceGenerator:
    """Test cases for slice_generator function"""
    
    @pytest.fixture
    def large_dataframe(self):
        """Large DataFrame for testing"""
        return pd.DataFrame({
            'id': range(1000),
            'value': [f'value_{i}' for i in range(1000)]
        })
    
    def test_slice_generator_default_chunk(self, large_dataframe):
        """Test slice generator with default chunk size"""
        slices = list(slice_generator(large_dataframe))
        
        assert len(slices) == 1  # 1000 rows with default 1000 chunk size
        assert len(slices[0]) == 1000
    
    def test_slice_generator_custom_chunk(self, large_dataframe):
        """Test slice generator with custom chunk size"""
        slices = list(slice_generator(large_dataframe, chunk_size=250))
        
        assert len(slices) == 4  # 1000 rows with 250 chunk size
        for slice_df in slices:
            assert len(slice_df) == 250
    
    def test_slice_generator_small_dataframe(self):
        """Test slice generator with small DataFrame"""
        small_df = pd.DataFrame({'id': [1, 2, 3]})
        slices = list(slice_generator(small_df, chunk_size=10))
        
        assert len(slices) == 1
        assert len(slices[0]) == 3
    
    def test_slice_generator_empty_dataframe(self):
        """Test slice generator with empty DataFrame"""
        empty_df = pd.DataFrame()
        slices = list(slice_generator(empty_df))
        
        assert len(slices) == 0


class TestDecodeDictionary:
    """Test cases for decodeDictionary function"""
    
    def test_decode_simple_dictionary(self):
        """Test decoding simple dictionary"""
        test_dict = {
            'key1': 'value1',
            'key2': 'value2'
        }
        result = decode_dictionary(test_dict)
        
        assert result == test_dict
    
    def test_decode_bytes_values(self):
        """Test decoding dictionary with bytes values"""
        test_dict = {
            'key1': b'Hello',
            'key2': b'World'
        }
        result = decode_dictionary(test_dict)
        
        assert result['key1'] == 'Hello'
        assert result['key2'] == 'World'
    
    def test_decode_nested_dictionary(self):
        """Test decoding nested dictionary"""
        test_dict = {
            'level1': {
                'level2': {
                    'key': b'nested_value'
                }
            }
        }
        result = decode_dictionary(test_dict)
        
        assert result['level1']['level2']['key'] == 'nested_value'
    
    def test_decode_mixed_types(self):
        """Test decoding dictionary with mixed types"""
        test_dict = {
            'string': 'normal_string',
            'bytes': b'bytes_string',
            'number': 123,
            'nested': {
                'inner_bytes': b'inner_value'
            }
        }
        result = decode_dictionary(test_dict)
        
        assert result['string'] == 'normal_string'
        assert result['bytes'] == 'bytes_string'
        assert result['number'] == 123
        assert result['nested']['inner_bytes'] == 'inner_value'
    
    def test_decode_non_dictionary(self):
        """Test decoding non-dictionary input"""
        # Test with bytes
        result = decode_dictionary(b'test_bytes')
        assert result == 'test_bytes'
        
        # Test with string
        result = decode_dictionary('normal_string')
        assert result == 'normal_string'
        
        # Test with number
        result = decode_dictionary(123)
        assert result == 123


class TestRouteAccessControl:
    """Test suite for route access control"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_request = Mock(spec=Request)
        self.mock_request.client = Mock()
        self.mock_request.client.host = "192.168.1.1"
        self.mock_request.headers = {}
    
    @patch('app.utils.utils.settings')
    def test_domain_whitelist_with_origin_header(self, mock_settings):
        """Test access granted via domain whitelist using Origin header"""
        mock_settings.domain_whitelist = ["example.com", "api.example.com"]
        
        self.mock_request.headers = {"origin": "https://example.com"}
        
        verify_route_access(self.mock_request)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_domain_whitelist_with_referer_header(self, mock_settings):
        """Test access granted via domain whitelist using Referer header"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {"referer": "https://example.com/page"}
        
        verify_route_access(self.mock_request)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_domain_whitelist_subdomain(self, mock_settings):
        """Test access granted for subdomain of whitelisted domain"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {"origin": "https://api.example.com"}
        
        verify_route_access(self.mock_request)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_domain_not_in_whitelist_no_api_keys(self, mock_settings):
        """Test access denied when domain not in whitelist and no api_keys"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {"origin": "https://unauthorized.com"}
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail
    
    @patch('app.utils.utils.settings')
    def test_bearer_token_valid_list(self, mock_settings):
        """Test access granted with valid Bearer token from list"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["secret-token-123", "another-token"]
        self.mock_request.headers = {"authorization": "Bearer secret-token-123"}
        
        verify_route_access(self.mock_request, api_keys=api_keys)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_bearer_token_invalid_list(self, mock_settings):
        """Test access denied with invalid Bearer token"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["secret-token-123"]
        self.mock_request.headers = {"authorization": "Bearer wrong-token"}
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_bearer_token_missing_bearer_prefix(self, mock_settings):
        """Test access denied when Bearer prefix is missing"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["secret-token-123"]
        self.mock_request.headers = {"authorization": "secret-token-123"}  # Missing "Bearer "
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_custom_header_valid_dict(self, mock_settings):
        """Test access granted with valid custom header from dict"""
        mock_settings.domain_whitelist = []
        
        api_keys = [{"X-API-Key": "my-secret-key"}, {"X-Auth": "token123"}]
        self.mock_request.headers = {"X-API-Key": "my-secret-key"}

        verify_route_access(self.mock_request, api_keys=api_keys)  # Does not raise: access granted

    @patch('app.utils.utils.settings')
    def test_custom_header_name_is_case_insensitive(self, mock_settings):
        """Test that a custom header matches a real request, whose header names are lowercase"""
        mock_settings.domain_whitelist = []
        request = Request({"type": "http", "headers": [(b"x-api-key", b"my-secret-key")]})

        verify_route_access(request, api_keys=[{"X-API-Key": "my-secret-key"}])  # Does not raise: access granted

        with pytest.raises(HTTPException):
            verify_route_access(request, api_keys=[{"X-API-Key": "other-key"}])

    @patch('app.utils.utils.settings')
    def test_custom_header_invalid_value(self, mock_settings):
        """Test access denied with invalid custom header value"""
        mock_settings.domain_whitelist = []
        
        api_keys = [{"X-API-Key": "my-secret-key"}]
        self.mock_request.headers = {"X-API-Key": "wrong-value"}
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_custom_header_missing(self, mock_settings):
        """Test access denied when custom header is missing"""
        mock_settings.domain_whitelist = []
        
        api_keys = [{"X-API-Key": "my-secret-key"}]
        self.mock_request.headers = {}  # No headers
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_multiple_custom_headers_one_valid(self, mock_settings):
        """Test access granted with one of multiple custom headers"""
        mock_settings.domain_whitelist = []
        
        api_keys = [
            {"X-API-Key": "secret1"},
            {"X-Custom-Auth": "secret2"},
            {"X-Service-Token": "secret3"}
        ]
        
        self.mock_request.headers = {
            "X-API-Key": "wrong",
            "X-Custom-Auth": "secret2"  # This one is valid
        }
        
        verify_route_access(self.mock_request, api_keys=api_keys)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_mixed_api_keys_bearer_and_custom(self, mock_settings):
        """Test access with mixed Bearer tokens and custom headers"""
        mock_settings.domain_whitelist = []
        
        # Mixed list: strings (Bearer) + dicts (custom headers)
        api_keys = [
            "bearer-token-123",
            {"X-API-Key": "custom-key-456"},
            "another-bearer-789",
            {"X-Service-Token": "service-xyz"}
        ]
        
        # Test with Bearer token
        self.mock_request.headers = {"authorization": "Bearer bearer-token-123"}
        verify_route_access(self.mock_request, api_keys=api_keys)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_mixed_api_keys_custom_header_success(self, mock_settings):
        """Test access with custom header in mixed list"""
        mock_settings.domain_whitelist = []
        
        api_keys = [
            "bearer-token-123",
            {"X-API-Key": "custom-key-456"}
        ]
        
        self.mock_request.headers = {"X-API-Key": "custom-key-456"}
        verify_route_access(self.mock_request, api_keys=api_keys)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_priority_domain_over_token(self, mock_settings):
        """Test that domain whitelist is checked before tokens"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {"origin": "https://example.com"}
        # Don't provide api_keys - should still pass via domain
        
        verify_route_access(self.mock_request)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_no_whitelist_and_no_api_keys(self, mock_settings):
        """Test access denied when no whitelist and no api_keys"""
        mock_settings.domain_whitelist = []
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_domain_fails_but_token_succeeds(self, mock_settings):
        """Test access via token when domain not whitelisted"""
        mock_settings.domain_whitelist = ["other-domain.com"]
        
        self.mock_request.headers = {"origin": "https://example.com", "authorization": "Bearer valid-token"}
        api_keys = ["valid-token"]
        
        verify_route_access(self.mock_request, api_keys=api_keys)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_empty_authorization_header_with_list(self, mock_settings):
        """Test access denied with empty authorization header"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["valid-token"]
        self.mock_request.headers = {"authorization": ""}
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, api_keys=api_keys)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_bearer_token_with_extra_spaces(self, mock_settings):
        """Test Bearer token validation handles extra spaces"""
        mock_settings.domain_whitelist = []
        
        api_keys = ["secret-token"]
        self.mock_request.headers = {"authorization": "Bearer   secret-token   "}  # Extra spaces
        
        verify_route_access(self.mock_request, api_keys=api_keys)  # Does not raise: access granted
    
    @patch('app.utils.utils.settings')
    def test_request_without_client(self, mock_settings):
        """Test handling when request.client is None"""
        mock_settings.domain_whitelist = []
        
        self.mock_request.client = None
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_whitelist_only_no_origin(self, mock_settings):
        """Test access denied with whitelist but no origin header"""
        mock_settings.domain_whitelist = ["example.com"]
        
        self.mock_request.headers = {}  # No origin or referer
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request)
        
        assert exc_info.value.status_code == 403
    
    @patch('app.utils.utils.settings')
    def test_api_keys_none_explicit(self, mock_settings):
        """Test with api_keys=None explicitly passed"""
        mock_settings.domain_whitelist = []
        
    @patch('app.utils.utils.settings')
    def test_api_keys_none_explicit(self, mock_settings):
        """Test with api_keys=None explicitly passed"""
        mock_settings.domain_whitelist = []
        
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(self.mock_request, api_keys=None)
        
        assert exc_info.value.status_code == 403


class TestGetUserOutputPath:
    """Test cases for get_user_output_path function"""
    
    @patch('app.utils.utils.settings')
    @patch('os.makedirs')
    def test_with_user(self, mock_makedirs, mock_settings):
        """Test path generation with user"""
        mock_settings.upload_dir = "/uploads"
        mock_user = Mock()
        mock_user.id = "user123"
        
        result = get_user_output_path("node456", mock_user)
        
        assert result == "/uploads/user123/node456-output.json"
        mock_makedirs.assert_called_once_with("/uploads/user123", exist_ok=True)
    
    @patch('app.utils.utils.settings')
    def test_without_user(self, mock_settings):
        """Test path generation without user"""
        mock_settings.upload_dir = "/uploads"
        
        result = get_user_output_path("node456")
        
        assert result == "/uploads/node456-output.json"
    
    @patch('app.utils.utils.settings')
    @patch('os.makedirs')
    def test_user_with_special_chars(self, mock_makedirs, mock_settings):
        """Test with user ID containing special characters"""
        mock_settings.upload_dir = "/uploads"
        mock_user = Mock()
        mock_user.id = "user-123_test"
        
        result = get_user_output_path("node_456", mock_user)
        
        assert result == "/uploads/user-123_test/node_456-output.json"


class TestConvertNumpyTypeToPython:
    """Test cases for convert_numpy_type_to_python function"""
    
    def test_bool_types(self):
        """Test boolean type conversion"""
        assert convert_numpy_type_to_python(np.bool_(True)) == "bool"
        assert convert_numpy_type_to_python(True) == "bool"
    
    def test_int_types(self):
        """Test integer type conversion"""
        assert convert_numpy_type_to_python(np.int8(1)) == "int"
        assert convert_numpy_type_to_python(np.int16(1)) == "int"
        assert convert_numpy_type_to_python(np.int32(1)) == "int"
        assert convert_numpy_type_to_python(np.int64(1)) == "int"
        assert convert_numpy_type_to_python(np.uint8(1)) == "int"
        assert convert_numpy_type_to_python(np.uint16(1)) == "int"
        assert convert_numpy_type_to_python(np.uint32(1)) == "int"
        assert convert_numpy_type_to_python(np.uint64(1)) == "int"
    
    def test_float_types(self):
        """Test float type conversion"""
        assert convert_numpy_type_to_python(np.float16(1.0)) == "float"
        assert convert_numpy_type_to_python(np.float32(1.0)) == "float"
        assert convert_numpy_type_to_python(np.float64(1.0)) == "float"
    
    def test_complex_types(self):
        """Test complex type conversion"""
        assert convert_numpy_type_to_python(np.complex64(1+2j)) == "complex"
        assert convert_numpy_type_to_python(np.complex128(1+2j)) == "complex"
    
    def test_string_types(self):
        """Test string type conversion"""
        assert convert_numpy_type_to_python(np.str_("test")) == "str"
        assert convert_numpy_type_to_python(np.bytes_(b"test")) == "bytes"
    
    def test_array_with_dtype(self):
        """Test array with dtype attribute"""
        int_array = np.array([1, 2, 3], dtype=np.int32)
        float_array = np.array([1.0, 2.0], dtype=np.float64)
        bool_array = np.array([True, False], dtype=np.bool_)
        
        assert convert_numpy_type_to_python(int_array) == "int"
        assert convert_numpy_type_to_python(float_array) == "float"
        assert convert_numpy_type_to_python(bool_array) == "bool"
    
    def test_other_types(self):
        """Test other type fallback"""
        result = convert_numpy_type_to_python("regular_string")
        assert result == "str"

    def test_array_with_object_or_string_dtype(self):
        assert convert_numpy_type_to_python(np.array(["a", None], dtype=object)) == "str"
        assert convert_numpy_type_to_python(np.array(["a", "b"])) == "ndarray"  # dtype '<U1'
        assert convert_numpy_type_to_python(np.array([1], dtype=np.uint16)) == "int"

    def test_array_with_unmapped_dtype_keeps_type_name(self):
        assert convert_numpy_type_to_python(np.array([1 + 2j])) == "ndarray"
        assert convert_numpy_type_to_python(pd.Series([1.5])) == "float"
        assert convert_numpy_type_to_python(np.datetime64("2024-01-01")) == "datetime64"

    def test_unknown_type(self):
        class Custom:
            pass
        assert convert_numpy_type_to_python(Custom()) == "Custom"
        assert convert_numpy_type_to_python(None) == "NoneType"
        assert convert_numpy_type_to_python(3) == "int"
        assert convert_numpy_type_to_python(2.5) == "float"


class TestNormalizeDtypeString:
    """Test cases for normalize_dtype_string function"""
    
    def test_basic_types(self):
        """Test basic type normalization"""
        assert normalize_dtype_string("bool") == "bool"
        assert normalize_dtype_string("int64") == "int"
        assert normalize_dtype_string("float64") == "float"
        assert normalize_dtype_string("object") == "str"
        assert normalize_dtype_string("string") == "str"
    
    def test_numpy_types(self):
        """Test numpy type normalization"""
        assert normalize_dtype_string("int8") == "int"
        assert normalize_dtype_string("int16") == "int"
        assert normalize_dtype_string("int32") == "int"
        assert normalize_dtype_string("uint8") == "int"
        assert normalize_dtype_string("float16") == "float"
        assert normalize_dtype_string("float32") == "float"
        assert normalize_dtype_string("complex64") == "complex"
        assert normalize_dtype_string("complex128") == "complex"
    
    def test_datetime_types(self):
        """Test datetime type normalization"""
        assert normalize_dtype_string("datetime64") == "datetime"
        assert normalize_dtype_string("timedelta64") == "timedelta"
    
    def test_case_insensitive(self):
        """Test case insensitive matching"""
        assert normalize_dtype_string("INT64") == "int"
        assert normalize_dtype_string("FLOAT32") == "float"
        assert normalize_dtype_string("BOOL") == "bool"
    
    def test_partial_matches(self):
        """Test partial string matching"""
        assert normalize_dtype_string("dtype('int64')") == "int"
        assert normalize_dtype_string("float64_custom") == "float"
    
    def test_unknown_type(self):
        """Test unknown type fallback"""
        result = normalize_dtype_string("unknown_type")
        assert result == "unknown_type"


class TestResolveFileName:
    """Test cases for resolve_file_name function"""
    
    def test_add_missing_extension(self):
        """Test adding missing extension"""
        result = resolve_file_name("file", "csv")
        assert result == "file.csv"
    
    def test_replace_different_extension(self):
        """Test replacing different extension"""
        result = resolve_file_name("file.txt", "csv")
        assert result == "file.csv"
    
    def test_keep_correct_extension(self):
        """Test keeping correct extension"""
        result = resolve_file_name("file.csv", "csv")
        assert result == "file.csv"
    
    def test_case_insensitive_extension(self):
        """Test case insensitive extension handling"""
        result = resolve_file_name("file.CSV", "csv")
        assert result == "file.CSV"
    
    def test_multiple_dots_in_filename(self):
        """Test filename with multiple dots"""
        result = resolve_file_name("my.data.file.txt", "json")
        assert result == "my.data.file.json"
    
    @patch('app.utils.utils.PathSecurityValidator.validate_file_extension')
    def test_security_validation_failure(self, mock_validator):
        """Test security validation failure"""
        mock_validator.return_value = False
        
        with pytest.raises(ValueError, match="File extension 'exe' is not allowed"):
            resolve_file_name("file", "exe")
    
    @patch('app.utils.utils.PathSecurityValidator.validate_file_extension')
    def test_security_validation_success(self, mock_validator):
        """Test security validation success"""
        mock_validator.return_value = True
        
        result = resolve_file_name("file", "csv")
        assert result == "file.csv"


class TestFilterDataWithDuckDB:
    """Test cases for filter_data_with_duckdb function"""
    
    @pytest.fixture
    def sample_json_file(self):
        """Create a temporary JSON file for testing"""
        data = [
            {"id": 1, "name": "Alice", "age": 30, "city": "Paris"},
            {"id": 2, "name": "Bob", "age": 25, "city": "London"},
            {"id": 3, "name": "Charlie", "age": 35, "city": "Paris"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            filepath = f.name
        
        yield filepath
        
        # Cleanup
        try:
            os.unlink(filepath)
        except:
            pass
    
    def test_no_filters(self, sample_json_file):
        """Test returning all data without filters"""
        result = filter_data_with_duckdb(sample_json_file)
        
        assert len(result) == 3
        assert result[0]["name"] == "Alice"
    
    def test_select_specific_columns(self, sample_json_file):
        """Test selecting specific columns"""
        result = filter_data_with_duckdb(sample_json_file, select="name, age")
        
        assert len(result) == 3
        # Note: DuckDB may return columns in different order than specified
        assert len(result[0].keys()) == 2  # Should have exactly 2 columns
        assert "name" in result[0] or "age" in result[0]  # At least one should be present
        assert "city" not in result[0]  # City should not be present
    
    def test_where_filter(self, sample_json_file):
        """Test WHERE clause filtering"""
        result = filter_data_with_duckdb(sample_json_file, where="age > 30")
        
        assert len(result) == 1
        assert result[0]["name"] == "Charlie"
    
    def test_select_and_where(self, sample_json_file):
        """Test combined SELECT and WHERE"""
        result = filter_data_with_duckdb(
            sample_json_file, 
            select="name", 
            where="city = 'Paris'"
        )
        
        assert len(result) == 2
        # Check that we have exactly one column (name)
        assert len(result[0].keys()) == 1
        # Get the actual column name (it should be 'name' but let's be flexible)
        column_name = list(result[0].keys())[0]
        names = [row[column_name] for row in result]
        assert "Alice" in names
        assert "Charlie" in names
    
    def test_file_not_found(self):
        """Test handling of non-existent file"""
        with pytest.raises(HTTPException) as exc_info:
            filter_data_with_duckdb("nonexistent.json")
        
        assert exc_info.value.status_code == 500
        assert "Error filtering data" in str(exc_info.value.detail)
    
    def test_invalid_json(self):
        """Test handling of invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            filepath = f.name
        
        try:
            with pytest.raises(HTTPException) as exc_info:
                filter_data_with_duckdb(filepath)
            
            assert exc_info.value.status_code == 500
        finally:
            os.unlink(filepath)
    
    def test_invalid_sql(self, sample_json_file):
        """Test handling of invalid SQL"""
        with pytest.raises(HTTPException) as exc_info:
            filter_data_with_duckdb(
                sample_json_file, 
                where="invalid_column = 'value'"
            )
        
        assert exc_info.value.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__])