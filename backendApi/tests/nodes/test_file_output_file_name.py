"""
The file output node writes in the upload folder of the user: its file name cannot carry a directory.
"""
import os
from unittest.mock import Mock

import pandas as pd
import pytest

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.outputs.file_output import FileOutput
from app.utils.utils import generate_pandas_schema

pytestmark = pytest.mark.asyncio


def file_output(file_name, upload_dir):
    node = FileOutput(id="out", data={"fileName": {"value": file_name}, "fileType": {"value": "csv"}})
    df = pd.DataFrame([{"a": 1}])
    node_input = Mock()
    node_input.get_connected_node.return_value = Mock()
    node_input.get_node_data.return_value = NodeDataPandasDf(nodeSchema=generate_pandas_schema(df), data=df, name="in")
    node.inputs = {"in": node_input}
    return node


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr("app.nodes.outputs.file_output.settings.upload_dir", str(uploads))
    return uploads


@pytest.mark.parametrize("file_name", ["../evil.csv", "../../evil", "sub/evil.csv", "..", "back\\slash.csv"])
async def test_file_name_with_a_directory_is_refused(upload_dir, tmp_path, file_name):
    node = file_output(file_name, upload_dir)

    assert await node.process() == StatusNode.Error
    assert "Invalid file name" in node.statusMessage
    written = [os.path.join(root, name) for root, _, names in os.walk(tmp_path) for name in names]
    assert written == []


async def test_absolute_file_name_is_refused(upload_dir, tmp_path):
    target = tmp_path / "elsewhere.csv"
    node = file_output(str(target), upload_dir)

    assert await node.process() == StatusNode.Error
    assert not target.exists()


async def test_plain_file_name_is_written_in_the_upload_folder(upload_dir):
    node = file_output("report", upload_dir)

    assert await node.process() == StatusNode.Valid
    assert pd.read_csv(upload_dir / "report.csv")["a"].tolist() == [1]
