"""
Tests of the workflow models
"""
from bson import ObjectId

from app.models.interface.workflow_interface import IProject


def test_valid_object_id_string_is_kept():
    object_id = str(ObjectId())

    assert IProject.prevent_auto_objectid(object_id) == object_id


def test_invalid_24_character_id_is_dropped():
    """A 24-character string that is not an ObjectId is replaced by None (InvalidId is caught)"""
    assert IProject.prevent_auto_objectid("z" * 24) is None


def test_generated_object_id_is_dropped():
    assert IProject.prevent_auto_objectid(ObjectId()) is None
