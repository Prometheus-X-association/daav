"""
Tests of POST /datasets/getContentDataset (the readers are mocked).
"""
import threading
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status

from app.models.interface.dataset_interface import ConnectionInfo, FileDataset, MongoDataset, Pagination
from app.routes import datasets


def connection_info(dataset):
    return ConnectionInfo.model_construct(
        dataset=dataset, pagination=Pagination.model_construct(page=1, perPage=10), datasetParams=None
    )


@pytest.mark.asyncio
async def test_synchronous_reader_runs_outside_event_loop_thread():
    """The synchronous MongoDB reader runs in the thread pool, not in the event loop thread"""
    dataset = MongoDataset.model_construct(id=None, type="mongo", name="m")
    reader_threads = []

    def fake_reader(*args):
        reader_threads.append(threading.current_thread())
        return {"data": []}

    with patch.object(datasets, "get_mongo_content", side_effect=fake_reader):
        result = await datasets.get_content_dataset(Mock(), connection_info(dataset), Mock(username="alice"))

    assert result == {"data": []}
    assert reader_threads and reader_threads[0] is not threading.current_thread()


@pytest.mark.asyncio
async def test_dataframe_reader_runs_outside_event_loop_thread():
    """get_df_content_dataset also runs the synchronous MongoDB reader in the thread pool"""
    dataset = MongoDataset.model_construct(id=None, type="mongo", name="m")
    reader_threads = []

    def fake_reader(*args):
        reader_threads.append(threading.current_thread())
        return "dataframe"

    with patch.object(datasets.dataset_service, "getDfMongoContent", side_effect=fake_reader):
        result = await datasets.get_df_content_dataset(Mock(), connection_info(dataset), Mock(username="alice"))

    assert result == "dataframe"
    assert reader_threads and reader_threads[0] is not threading.current_thread()


@pytest.mark.asyncio
async def test_file_access_denied_is_logged_and_returned():
    """A denied file access is logged as read_failed and returned as 403"""
    dataset = FileDataset.model_construct(id=None, type="file", name="f", folder=None, filePath="/forbidden.csv")
    denied = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission error")
    request = Mock()
    request.client.host = "10.0.0.1"

    with patch.object(datasets, "get_file_content", side_effect=denied), \
         patch.object(datasets, "log_file_access") as log_file_access:
        with pytest.raises(HTTPException) as exc_info:
            await datasets.get_content_dataset(request, connection_info(dataset), Mock(username="alice"))

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    log_file_access.assert_called_with("10.0.0.1", "/forbidden.csv", "read_failed")


@pytest.mark.asyncio
async def test_uploaded_file_is_written_outside_event_loop_thread(tmp_path):
    """The uploaded file is written to disk in the thread pool, with the uploaded content"""
    upload = Mock(filename="data.csv")
    upload.read = AsyncMock(return_value=b"a,b\n1,2\n")
    writer_threads = []
    original_write_bytes = datasets.Path.write_bytes

    def tracking_write_bytes(path, content):
        writer_threads.append(threading.current_thread())
        return original_write_bytes(path, content)

    with patch.object(datasets, "UPLOAD_DIR", tmp_path), \
         patch.object(datasets.Path, "write_bytes", tracking_write_bytes):
        result = await datasets._save_upload_file(upload, Mock(id="user-1", username="alice"))

    assert (tmp_path / "user-1" / "data.csv").read_bytes() == b"a,b\n1,2\n"
    assert result["filepath"].endswith("data.csv")
    assert writer_threads and writer_threads[0] is not threading.current_thread()
