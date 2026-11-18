"""
Tests for the JSON conversion of the example data held by NodeDataPandasDf.
"""
import numpy
import pandas as pd
import pytest
from bson import ObjectId

from app.models.interface.node_data import NodeDataPandasDf
from app.utils.utils import generate_pandas_schema


@pytest.fixture
def node_data():
    return NodeDataPandasDf(nodeSchema=generate_pandas_schema(pd.DataFrame([{"a": 1}])), name="n")


def test_object_id_becomes_a_string(node_data):
    oid = ObjectId("65a1b2c3d4e5f6a7b8c9d0e1")
    assert node_data._convert_objectid(oid) == "65a1b2c3d4e5f6a7b8c9d0e1"


def test_ndarray_becomes_a_list(node_data):
    assert node_data._convert_objectid(numpy.array([1, 2])) == [1, 2]


@pytest.mark.parametrize("value, expected, expected_type", [
    (numpy.int8(-3), -3, int),
    (numpy.uint64(7), 7, int),
    (numpy.float16(0.5), 0.5, float),
    (numpy.float64(1.25), 1.25, float),
    (numpy.bool_(False), False, bool),
    (numpy.str_("abc"), "abc", str),
    (numpy.complex64(1 + 2j), 1 + 2j, complex),
    (numpy.bytes_(b"xy"), b"xy", bytes),
])
def test_numpy_scalars(node_data, value, expected, expected_type):
    result = node_data._convert_objectid(value)
    assert result == expected
    assert type(result) is expected_type


def test_numpy_datetime_uses_item(node_data):
    day = numpy.datetime64("2024-01-02")
    assert node_data._convert_objectid(day) == day.item()


def test_nested_dict_and_list(node_data):
    oid = ObjectId("65a1b2c3d4e5f6a7b8c9d0e1")
    value = {"a": [oid, {"b": numpy.int32(2)}], "c": {"d": [numpy.float32(0.25), "x"]}}
    assert node_data._convert_objectid(value) == {
        "a": ["65a1b2c3d4e5f6a7b8c9d0e1", {"b": 2}],
        "c": {"d": [0.25, "x"]},
    }


def test_tuple_and_plain_values_are_unchanged(node_data):
    value = (numpy.int64(1),)
    assert node_data._convert_objectid(value) is value
    assert node_data._convert_objectid("x") == "x"
    assert node_data._convert_objectid(None) is None
    timestamp = pd.Timestamp("2024-01-01")
    assert node_data._convert_objectid(timestamp) is timestamp


def test_serialize_data_example(node_data):
    df = pd.DataFrame({"id": [ObjectId("65a1b2c3d4e5f6a7b8c9d0e1")], "n": [numpy.int64(4)]})
    assert node_data.serialize_data_example(df, None) == {
        "id": {0: "65a1b2c3d4e5f6a7b8c9d0e1"},
        "n": {0: 4},
    }
    assert node_data.serialize_data_example(None, None) is None
