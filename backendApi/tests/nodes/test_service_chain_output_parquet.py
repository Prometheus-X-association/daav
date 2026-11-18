"""
The service chain output node sends the rows of a parquet input (it used to fail on every parquet input).
"""
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pyarrow.parquet as pq
import pytest

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataParquet
from app.nodes.outputs.service_chain_output import ServiceChainOutput

pytestmark = pytest.mark.asyncio

ROWS = [{"a": i, "b": f"row{i}"} for i in range(50)]


@pytest.fixture
def post():
    with patch("requests.post") as post:
        yield post


def service_chain_output(tmp_path):
    path = str(tmp_path / "in.parquet")
    pd.DataFrame(ROWS).to_parquet(path)
    node_input = Mock()
    node_input.get_connected_node.return_value = Mock()
    node_input.get_node_data.return_value = NodeDataParquet(data=path, nodeSchema=pq.ParquetFile(path).schema, name="in")

    node = ServiceChainOutput(id="chain-out", data={"selectDataSource": {"value": "ds1"}})
    node.datasetService = Mock(
        get_dataset=AsyncMock(return_value=Mock(url="http://pdc.example.com")),
        pdcChainHeaders=Mock(x_ptx_service_chain_id="chain", x_ptx_target_id="target"),
    )
    node.inputs = {"in": node_input}
    return node


async def test_parquet_rows_are_sent(post, tmp_path):
    node = service_chain_output(tmp_path)

    assert await node.process() == StatusNode.Valid
    assert post.call_args.args[0] == "http://pdc.example.com/service-chain/resume"
    body = post.call_args.kwargs["json"]
    assert (body["chainId"], body["targetId"]) == ("chain", "target")
    assert body["data"] == ROWS


async def test_parquet_sample_sends_the_first_20_rows(post, tmp_path):
    node = service_chain_output(tmp_path)

    assert await node.process(sample=True) == StatusNode.Valid
    assert post.call_args.kwargs["json"]["data"] == ROWS[:20]
