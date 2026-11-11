"""
Edge cases of the dataset readers that used to end in an HTTP 500.
"""
import httpx
import pytest
from fastapi import HTTPException

from app.models.interface.dataset_interface import FileDataset, Pagination
from app.routes.datasets import _parse_custom_api, api_content, csv_file
from app.services.dataset_service import DatasetService

PAGE = Pagination(page=1, perPage=10)


def custom_api_page(**links):
    return {"data": [{"id": 1}], "count": 1, "self": {"href": "https://api.example.com/items?page=2"}, **links}


def test_api_response_without_content_type_is_read_as_xml():
    response = httpx.Response(200, content=b"<rows><row><a>1</a><b>x</b></row></rows>")
    assert "content-type" not in response.headers
    assert api_content(response) == [{"a": "1", "b": "x"}]


def test_api_response_in_an_unknown_format_is_a_422():
    response = httpx.Response(200, content=b"neither json nor xml")
    with pytest.raises(HTTPException) as error:
        api_content(response)
    assert error.value.status_code == 422


@pytest.mark.parametrize("key", ["prev", "previous"])
def test_custom_api_previous_link(key):
    data = custom_api_page(**{key: {"href": "https://api.example.com/items?page=1"}})
    assert _parse_custom_api(data, PAGE).prev_url == "https://api.example.com/items?page=1"


def test_custom_api_without_previous_link():
    assert _parse_custom_api(custom_api_page(), PAGE).prev_url is None


def test_csv_row_longer_than_the_header_keeps_its_extra_values(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1,2\n3,4,5,x\n")
    assert csv_file(str(path), "true", ",") == [
        {"a": 1, "b": 2},
        {"a": 3, "b": 4, "_extra": [5, "x"]},
    ]


def test_tsv_without_header_setting_uses_the_first_row_like_a_csv(tmp_path):
    path = tmp_path / "data.tsv"
    path.write_text("a\tb\n1\t2\n")
    dataset = FileDataset.model_construct(id="ds1", type="file", name="t", filePath=str(path), folder=None,
                                          csvHeader=None, csvDelimiter=None)
    node_data = DatasetService().getDfFileContentData(dataset)
    assert node_data.data.to_dict(orient="records") == [{"a": 1, "b": 2}]
