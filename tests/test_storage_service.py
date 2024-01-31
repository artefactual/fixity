import json
from unittest import mock

import pytest
import requests

from fixity import storage_service
from fixity.models import Session
from fixity.utils import InvalidUUID


SESSION = Session()
STORAGE_SERVICE_URL = "http://localhost:8000/"
STORAGE_SERVICE_USER = "test"
STORAGE_SERVICE_KEY = "dfe83300db5f05f63157f772820bb028bd4d0e27"


# Single AIP


@mock.patch(
    "requests.get",
    side_effect=[
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {
                    "uuid": "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
                },
            },
            spec=requests.Response,
        )
    ],
)
def test_get_single_aip(_get):
    aip_uuid = "a7f2a05b-0fdf-42f1-a46c-4522a831cf17"
    aip = storage_service.get_single_aip(
        aip_uuid, STORAGE_SERVICE_URL, STORAGE_SERVICE_USER, STORAGE_SERVICE_KEY
    )
    assert isinstance(aip, dict)
    assert aip["uuid"] == aip_uuid


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=404, spec=requests.Response)]
)
def test_single_aip_raises_on_404(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_single_aip(
            "ba31d9b8-5baa-4d62-839e-cf71497d4acf",
            STORAGE_SERVICE_URL,
            STORAGE_SERVICE_USER,
            STORAGE_SERVICE_KEY,
        )

    assert "returned 404" in str(ex.value)
    assert ex.value.report is None


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=500, spec=requests.Response)]
)
def test_single_aip_raises_on_500(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_single_aip(
            "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
            STORAGE_SERVICE_URL,
            STORAGE_SERVICE_USER,
            STORAGE_SERVICE_KEY,
        )

    assert "internal error" in str(ex.value)
    assert ex.value.report is None


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=504, spec=requests.Response)]
)
def test_single_aip_raises_on_504(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_single_aip(
            "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
            STORAGE_SERVICE_URL,
            STORAGE_SERVICE_USER,
            STORAGE_SERVICE_KEY,
        )

    assert "gateway timeout" in str(ex.value)
    assert ex.value.report is None


def test_single_aip_raises_with_invalid_uuid():
    with pytest.raises(InvalidUUID):
        storage_service.get_single_aip(
            "foo", STORAGE_SERVICE_URL, STORAGE_SERVICE_USER, STORAGE_SERVICE_KEY
        )


def test_single_aip_raises_with_invalid_url():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_single_aip(
            "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
            "http://foo",
            STORAGE_SERVICE_USER,
            STORAGE_SERVICE_KEY,
        )

    error_msgs = ("Unable to connect", "returned 404", "returned 410")
    assert any(msg in str(ex.value) for msg in error_msgs)


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=401, spec=requests.Response)]
)
def test_single_aip_raises_with_invalid_auth(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_single_aip(
            "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
            STORAGE_SERVICE_URL,
            STORAGE_SERVICE_USER,
            "bad_key",
        )

    assert "failed authentication" in str(ex.value)


# All AIPs


@mock.patch(
    "requests.get",
    side_effect=[
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {
                    "meta": {"next": None},
                    "objects": [
                        {
                            "package_type": "AIP",
                            "status": "UPLOADED",
                            "uuid": "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
                        },
                        {
                            "package_type": "AIP",
                            "status": "UPLOADED",
                            "uuid": "c8ebb75e-6b7a-46dd-a360-91d3753d7b72",
                        },
                    ],
                },
            },
            spec=requests.Response,
        )
    ],
)
def test_get_all_aips(_get):
    aip_uuids = (
        "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
        "c8ebb75e-6b7a-46dd-a360-91d3753d7b72",
    )

    aips = storage_service.get_all_aips(
        STORAGE_SERVICE_URL, STORAGE_SERVICE_USER, STORAGE_SERVICE_KEY
    )
    assert len(aips) == 2
    for aip in aips:
        assert isinstance(aip, dict)
        assert aip["uuid"] in aip_uuids


@mock.patch(
    "requests.get",
    side_effect=[
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"meta": {"next": None}, "objects": []},
            },
            spec=requests.Response,
        )
    ],
)
def test_get_all_aips_gets_uploaded_aips_only(_get):
    aips = storage_service.get_all_aips(
        STORAGE_SERVICE_URL, STORAGE_SERVICE_USER, STORAGE_SERVICE_KEY
    )
    non_uploaded = list(filter(lambda a: a["status"] != "UPLOADED", aips))
    assert len(non_uploaded) == 0


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=500, spec=requests.Response)]
)
def test_get_all_aips_raises_on_500(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_all_aips(
            STORAGE_SERVICE_URL, STORAGE_SERVICE_USER, STORAGE_SERVICE_KEY
        )

    assert "internal error" in str(ex.value)
    assert ex.value.report is None


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=504, spec=requests.Response)]
)
def test_get_all_aips_raises_on_504(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_all_aips(
            STORAGE_SERVICE_URL, STORAGE_SERVICE_USER, STORAGE_SERVICE_KEY
        )

    assert "gateway timeout" in str(ex.value)
    assert ex.value.report is None


def test_get_all_aips_raises_with_invalid_url():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_all_aips(
            "http://foo", STORAGE_SERVICE_USER, STORAGE_SERVICE_KEY
        )

    error_msgs = ("Unable to connect", "returned 404", "returned 410")
    assert any(msg in str(ex.value) for msg in error_msgs)


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=401, spec=requests.Response)]
)
def test_get_all_aips_raises_with_bad_auth(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_all_aips(
            STORAGE_SERVICE_URL, STORAGE_SERVICE_USER, "bad_key"
        )

    assert "failed authentication" in str(ex.value)


# Fixity scan


@mock.patch(
    "requests.get",
    side_effect=[
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {
                    "failures": {
                        "files": {"untracked": [], "changed": [], "missing": []}
                    },
                    "message": "",
                    "success": True,
                },
            },
            spec=requests.Response,
        )
    ],
)
def test_successful_fixity_scan(_get):
    success, report = storage_service.scan_aip(
        "c8ebb75e-6b7a-46dd-a360-91d3753d7b72",
        STORAGE_SERVICE_URL,
        STORAGE_SERVICE_USER,
        STORAGE_SERVICE_KEY,
        SESSION,
    )

    assert success is True
    assert report.success is True

    parsed_report = json.loads(report.report)
    for category in ("untracked", "changed", "missing"):
        assert len(parsed_report["failures"]["files"][category]) == 0


@mock.patch(
    "requests.get",
    side_effect=[
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {
                    "failures": {
                        "files": {
                            "untracked": [],
                            "changed": [
                                {"path": "data/objects/oakland03.jp2"},
                                {"path": "manifest-sha512.txt"},
                            ],
                            "missing": [],
                        }
                    },
                    "message": "invalid bag",
                    "success": False,
                },
            },
            spec=requests.Response,
        )
    ],
)
def test_failed_fixity_scan(_get):
    success, report = storage_service.scan_aip(
        "c8ebb75e-6b7a-46dd-a360-91d3753d7b72",
        STORAGE_SERVICE_URL,
        STORAGE_SERVICE_USER,
        STORAGE_SERVICE_KEY,
        SESSION,
    )
    assert success is False
    assert report.success is False

    parsed_report = json.loads(report.report)
    assert len(parsed_report["failures"]["files"]["changed"]) == 2
    assert (
        parsed_report["failures"]["files"]["changed"][0]["path"]
        == "data/objects/oakland03.jp2"
    )
    for category in ("untracked", "missing"):
        assert len(parsed_report["failures"]["files"][category]) == 0


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=500, spec=requests.Response)]
)
def test_fixity_scan_raises_on_500(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.scan_aip(
            "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
            STORAGE_SERVICE_URL,
            STORAGE_SERVICE_USER,
            STORAGE_SERVICE_KEY,
            SESSION,
        )

    assert "internal error" in str(ex.value)


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=504, spec=requests.Response)]
)
def test_fixity_scan_raises_on_non_200(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.scan_aip(
            "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
            STORAGE_SERVICE_URL,
            STORAGE_SERVICE_USER,
            STORAGE_SERVICE_KEY,
            SESSION,
        )

    assert "returned 504" in str(ex.value)


def test_fixity_scan_raises_on_invalid_url():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.scan_aip(
            "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
            "http://foo",
            STORAGE_SERVICE_USER,
            STORAGE_SERVICE_KEY,
            SESSION,
        )

    error_msgs = (
        "Unable to connect",
        "fixity scan could not be started",
        "returned 410",
    )
    assert any(msg in str(ex.value) for msg in error_msgs)


@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=401, spec=requests.Response)]
)
def test_fixity_scan_raises_with_bad_auth(_get):
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.scan_aip(
            "a7f2a05b-0fdf-42f1-a46c-4522a831cf17",
            STORAGE_SERVICE_URL,
            STORAGE_SERVICE_USER,
            "bad_key",
            SESSION,
        )

    assert "failed authentication" in str(ex.value)
