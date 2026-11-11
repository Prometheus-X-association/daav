"""
Refusal cases of the access controls: route access, M2M credentials and file paths.
"""
import os
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.datastructures import Headers

from app.models.interface.user_interface import UserConfig
from app.utils.auth_utils import authenticate_m2m_credentials
from app.utils.security import PathSecurityValidator
from app.utils.utils import verify_route_access


def _request(headers: dict, client=("10.0.0.1", 1234)) -> Request:
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": client,
    }
    return Request(scope)


# ===========================
# verify_route_access
# ===========================

class TestVerifyRouteAccess:

    @pytest.fixture(autouse=True)
    def whitelist(self):
        with patch("app.utils.utils.settings") as mock_settings:
            mock_settings.domain_whitelist = ["example.com"]
            yield mock_settings

    def _denied(self, request, api_keys=None):
        with pytest.raises(HTTPException) as exc_info:
            verify_route_access(request, api_keys=api_keys)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access denied. Valid authentication required."

    @pytest.mark.parametrize("origin", [
        "https://evil-example.com",
        "https://example.com.evil.org",
        "https://notexample.com",
        "https://example.com:8443",
    ])
    def test_lookalike_domain_refused(self, origin):
        self._denied(_request({"origin": origin}))

    @pytest.mark.parametrize("origin", ["https://example.com", "https://api.example.com", "http://a.b.example.com/x"])
    def test_domain_and_subdomain_accepted(self, origin):
        assert verify_route_access(_request({"origin": origin})) is None

    def test_referer_without_scheme(self):
        assert verify_route_access(_request({"referer": "example.com/page"})) is None
        assert verify_route_access(_request({"referer": "sub.example.com"})) is None
        self._denied(_request({"referer": "evil.com/example.com"}))

    def test_origin_takes_precedence_over_referer(self):
        self._denied(_request({"origin": "https://evil.com", "referer": "https://example.com/"}))

    def test_whitelisted_origin_skips_api_keys(self):
        assert verify_route_access(_request({"origin": "https://example.com"}), api_keys=["t"]) is None

    def test_empty_whitelist_ignores_origin(self, whitelist):
        whitelist.domain_whitelist = []
        self._denied(_request({"origin": "https://example.com"}))

    def test_no_origin_and_no_keys(self):
        self._denied(_request({}))
        self._denied(_request({}), api_keys=[])
        self._denied(_request({}, client=None))

    def test_dict_key_without_authorization_header(self):
        request = _request({"x-api-key": "k"})
        assert verify_route_access(request, api_keys=[{"X-API-Key": "k"}]) is None
        self._denied(_request({}), api_keys=[{"X-API-Key": "k"}])

    def test_dict_key_does_not_match_the_authorization_header(self):
        self._denied(_request({"authorization": "Bearer k"}), api_keys=[{"X-API-Key": "k"}])

    def test_bearer_token(self):
        assert verify_route_access(_request({"authorization": "Bearer  tok  "}), api_keys=["tok"]) is None
        self._denied(_request({"authorization": "bearer tok"}), api_keys=["tok"])
        self._denied(_request({"authorization": "Basic tok"}), api_keys=["tok"])
        self._denied(_request({"x-api-key": "tok"}), api_keys=["tok"])

    def test_mixed_keys_and_unsupported_key_types(self):
        request = _request({"authorization": "Bearer tok"})
        assert verify_route_access(request, api_keys=[123, {"X-Other": "v"}, "tok"]) is None
        self._denied(request, api_keys=[123, None, ["tok"]])

    def test_dict_key_with_several_headers(self):
        api_keys = [{"X-A": "a", "X-B": "b"}]
        assert verify_route_access(_request({"x-b": "b"}), api_keys=api_keys) is None
        self._denied(_request({"x-a": "b"}), api_keys=api_keys)


# ===========================
# authenticate_m2m_credentials
# ===========================

def _user(name, credentials, active=True, config=True):
    user = Mock()
    user.username = name
    user.is_active = active
    user.config = UserConfig(credentials=credentials) if config else None
    return user


class TestAuthenticateM2mCredentials:

    def test_inactive_user(self):
        user = _user("u", {"x-key": "v"}, active=False)
        assert authenticate_m2m_credentials(Headers({"x-key": "v"}), [user]) == []

    @pytest.mark.parametrize("config, credentials", [(False, None), (True, {})])
    def test_user_without_configuration(self, config, credentials):
        user = _user("u", credentials, config=config)
        assert authenticate_m2m_credentials(Headers({"x-key": "v"}), [user]) == []

    def test_user_with_null_credentials(self):
        user = _user("u", None, config=False)
        user.config = Mock(credentials=None)
        assert authenticate_m2m_credentials(Headers({"x-key": "v"}), [user]) == []

    def test_header_name_case(self):
        user = _user("u", {"X-Service-Key": "v"})
        result = authenticate_m2m_credentials(Headers({"x-SERVICE-key": "v"}), [user])
        assert result == [{"user": user, "matched_credentials": {"X-Service-Key": "v"}}]

    def test_header_name_case_with_a_plain_dict(self):
        user = _user("u", {"x-key": "v"})
        result = authenticate_m2m_credentials({"X-KEY": "v"}, [user])
        assert result == [{"user": user, "matched_credentials": {"x-key": "v"}}]

    def test_first_matching_header_name_wins(self):
        user = _user("u", {"x-key": "v"})
        assert authenticate_m2m_credentials({"X-KEY": "other", "x-key": "v"}, [user]) == []

    def test_header_value_is_case_sensitive(self):
        user = _user("u", {"x-key": "Value"})
        assert authenticate_m2m_credentials(Headers({"x-key": "value"}), [user]) == []

    def test_empty_values(self):
        assert authenticate_m2m_credentials(Headers({"x-key": ""}), [_user("u", {"x-key": ""})]) == []
        assert authenticate_m2m_credentials(Headers({"x-key": "v"}), [_user("u", {"x-key": ""})]) == []

    def test_several_users_one_valid(self):
        inactive = _user("inactive", {"x-key": "v"}, active=False)
        no_config = _user("no_config", None, config=False)
        wrong = _user("wrong", {"x-key": "w"})
        valid = _user("valid", {"x-key": "v", "x-other": "o"})
        result = authenticate_m2m_credentials(Headers({"x-key": "v"}), [inactive, no_config, wrong, valid])
        assert result == [{"user": valid, "matched_credentials": {"x-key": "v"}}]

    def test_several_users_valid(self):
        first = _user("first", {"x-key": "v"})
        second = _user("second", {"x-key": "v", "x-other": "o"})
        result = authenticate_m2m_credentials(Headers({"x-key": "v", "x-other": "o"}), [first, second])
        assert result == [
            {"user": first, "matched_credentials": {"x-key": "v"}},
            {"user": second, "matched_credentials": {"x-key": "v", "x-other": "o"}},
        ]

    def test_error_returns_no_user(self):
        user = _user("u", {"x-key": "v"})
        user.config = Mock()
        user.config.credentials = {"x-key": 3}
        assert authenticate_m2m_credentials(Headers({"x-key": "v"}), [user]) == []


# ===========================
# PathSecurityValidator.validate_file_path
# ===========================

@pytest.fixture
def enable_security():
    PathSecurityValidator.set_security_enabled(True)
    yield
    PathSecurityValidator.reset_security_state()


class TestValidateFilePath:

    def _status(self, path, base_dir=None):
        with pytest.raises(HTTPException) as exc_info:
            PathSecurityValidator.validate_file_path(path, base_dir)
        return exc_info.value.status_code, exc_info.value.detail

    @pytest.mark.parametrize("path, pattern", [
        ("../secret.csv", r"\.\."),
        ("/etc/passwd", "/etc/"),
        ("data/$HOME/x.csv", r"\$"),
        ("data/x....csv", r"\.\."),
    ])
    def test_dangerous_path_with_and_without_base_dir(self, enable_security, tmp_path, path, pattern):
        assert self._status(path) == (400, f"Dangerous path pattern detected: {pattern}")
        assert self._status(path, str(tmp_path)) == (403, f"Dangerous path pattern detected: {pattern}")

    def test_encoded_traversal(self, enable_security, tmp_path):
        # The encoded form is caught on the original path, before the decoded variant
        assert self._status("data/%2e%2e/secret.csv") == (400, "Dangerous path pattern detected: %2e%2e")
        assert self._status("data/%2E%2E/secret.csv", str(tmp_path)) == (
            403, "Dangerous path pattern detected: %2e%2e")
        # A '..' that only appears once decoded is caught on the decoded variant
        assert self._status(".%2e/secret.csv") == (400, r"Dangerous path pattern detected: \.\.")
        assert self._status("data/%252e%252e/x") == (400, "Dangerous path pattern detected: %252e")

    def test_empty_path_and_null_byte(self, enable_security, tmp_path):
        assert self._status("") == (400, "File path cannot be empty")
        assert self._status("", str(tmp_path)) == (400, "File path cannot be empty")
        assert self._status("a\x00.csv", str(tmp_path)) == (400, "Null byte injection detected in file path")

    @pytest.mark.parametrize("char", ["<", ">", "|", "*", "?", '"'])
    def test_invalid_characters(self, enable_security, tmp_path, char):
        assert self._status(f"data/a{char}b.csv") == (400, "Invalid characters in file path")
        assert self._status(f"data/a{char}b.csv", str(tmp_path)) == (400, "Invalid characters in file path")

    def test_relative_path_resolved_under_base_dir(self, enable_security, tmp_path):
        result = PathSecurityValidator.validate_file_path("sub/./dir//file.csv", str(tmp_path))
        assert result == str((tmp_path / "sub" / "dir" / "file.csv").resolve())

    def test_absolute_path_inside_base_dir(self, enable_security, tmp_path):
        inside = str(tmp_path / "file.csv")
        assert PathSecurityValidator.validate_file_path(inside, str(tmp_path)) == str((tmp_path / "file.csv").resolve())

    def test_absolute_path_outside_base_dir(self, enable_security, tmp_path):
        base = tmp_path / "base"
        base.mkdir()
        outside = str(tmp_path / "other" / "file.csv")
        assert self._status(outside, str(base)) == (403, "Access outside base directory not allowed")

    def test_symlink_escaping_base_dir(self, enable_security, tmp_path):
        base = tmp_path / "base"
        base.mkdir()
        (tmp_path / "outside").mkdir()
        os.symlink(tmp_path / "outside", base / "link")
        assert self._status("link/file.csv", str(base)) == (403, "Access outside base directory not allowed")

    def test_dot_dot_that_stays_inside_is_normalized(self, enable_security, tmp_path):
        assert PathSecurityValidator.validate_file_path("data/../file.csv") == "file.csv"
        assert PathSecurityValidator.validate_file_path("data/../file.csv", str(tmp_path)) == str(
            (tmp_path / "file.csv").resolve())

    def test_without_base_dir_the_normalized_path_is_returned(self, enable_security):
        assert PathSecurityValidator.validate_file_path("data//sub/./file.csv") == os.path.normpath("data/sub/file.csv")

    def test_resolution_error_is_a_400(self, enable_security, tmp_path):
        with patch("app.utils.security.Path.resolve", side_effect=OSError("boom")):
            assert self._status("file.csv", str(tmp_path)) == (400, "Invalid path: boom")
