"""
A path is inside a directory only if it is that directory or below it:
a sibling directory whose name starts the same way is outside.
"""
import pytest
from fastapi import HTTPException

from app.utils.security import FileAccessController, PathSecurityValidator


@pytest.fixture
def enable_security():
    PathSecurityValidator.set_security_enabled(True)
    yield
    PathSecurityValidator.reset_security_state()


@pytest.fixture
def directories(tmp_path):
    base = tmp_path / "base"
    sibling = tmp_path / "base_evil"
    base.mkdir()
    sibling.mkdir()
    (base / "ok.csv").write_text("a\n1\n")
    (sibling / "secret.csv").write_text("a\n1\n")
    return base, sibling


def test_file_below_an_allowed_directory_can_be_read(enable_security, directories):
    base, _ = directories
    assert FileAccessController.can_read_file(str(base / "ok.csv"), [str(base)])
    assert FileAccessController.can_read_file(str(base), [str(base)])


def test_sibling_directory_with_the_same_prefix_cannot_be_read(enable_security, directories):
    base, sibling = directories
    assert not FileAccessController.can_read_file(str(sibling / "secret.csv"), [str(base)])


def test_path_below_the_base_directory_is_resolved(enable_security, directories):
    base, _ = directories
    assert PathSecurityValidator.validate_file_path("ok.csv", str(base)) == str(base / "ok.csv")


def test_absolute_path_to_a_sibling_directory_is_refused(enable_security, directories):
    base, sibling = directories
    with pytest.raises(HTTPException) as error:
        PathSecurityValidator.validate_file_path(str(sibling / "secret.csv"), str(base))
    assert error.value.status_code == 403
