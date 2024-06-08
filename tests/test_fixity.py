import json
import sys
import uuid
from datetime import datetime
from datetime import timezone
from unittest import mock

import pytest
import requests

from fixity import fixity
from fixity import reporting
from fixity.models import Report
from fixity.models import Session

SESSION = Session()
STORAGE_SERVICE_URL = "http://localhost:8000/"
STORAGE_SERVICE_USER = "test"
STORAGE_SERVICE_KEY = "test"
REPORT_URL = "http://localhost:8003/"

mock_scan_aip = mock.Mock(
    **{
        "status_code": 200,
        "json.return_value": {
            "success": True,
            "message": "",
            "failures": {"files": {"missing": [], "changed": [], "untracked": []}},
            "timestamp": None,
        },
    },
    spec=requests.Response,
)


@pytest.fixture
def mock_check_fixity():
    return [
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {},
            },
            spec=requests.Response,
        ),
        mock_scan_aip,
    ]


@mock.patch("requests.get")
def test_scan(_get, mock_check_fixity):
    _get.side_effect = mock_check_fixity
    aip_id = uuid.uuid4()

    response = fixity.scan(
        aip=str(aip_id),
        ss_url=STORAGE_SERVICE_URL,
        ss_user=STORAGE_SERVICE_USER,
        ss_key=STORAGE_SERVICE_KEY,
        session=SESSION,
    )

    assert response is True

    assert _get.mock_calls == [
        mock.call(
            f"{STORAGE_SERVICE_URL}api/v2/file/{aip_id}/",
            params={"username": STORAGE_SERVICE_USER, "api_key": STORAGE_SERVICE_KEY},
        ),
        mock.call(
            f"{STORAGE_SERVICE_URL}api/v2/file/{aip_id}/check_fixity/",
            params={"username": STORAGE_SERVICE_USER, "api_key": STORAGE_SERVICE_KEY},
        ),
    ]


@mock.patch("fixity.utils.utcnow")
@mock.patch("requests.get")
@mock.patch(
    "requests.post",
    side_effect=[
        mock.Mock(status_code=201, spec=requests.Response),
        mock.Mock(status_code=201, spec=requests.Response),
    ],
)
def test_scan_if_report_url_exists(_post, _get, utcnow, mock_check_fixity):
    _get.side_effect = mock_check_fixity
    start_time = 1514775600
    utcnow.return_value = datetime.fromtimestamp(start_time, timezone.utc)
    aip_id = uuid.uuid4()

    response = fixity.scan(
        aip=str(aip_id),
        ss_url=STORAGE_SERVICE_URL,
        ss_user=STORAGE_SERVICE_USER,
        ss_key=STORAGE_SERVICE_KEY,
        session=SESSION,
        report_url=REPORT_URL,
    )

    assert response is True

    assert _get.mock_calls == [
        mock.call(
            f"{STORAGE_SERVICE_URL}api/v2/file/{aip_id}/",
            params={"username": STORAGE_SERVICE_USER, "api_key": STORAGE_SERVICE_KEY},
        ),
        mock.call(
            f"{STORAGE_SERVICE_URL}api/v2/file/{aip_id}/check_fixity/",
            params={"username": STORAGE_SERVICE_USER, "api_key": STORAGE_SERVICE_KEY},
        ),
    ]
    assert _post.mock_calls == [
        mock.call(
            f"{REPORT_URL}api/fixity/{aip_id}",
            data=json.dumps({"started": start_time}),
            headers={"Content-Type": "application/json"},
        ),
        mock.call(
            f"{REPORT_URL}api/fixity/{aip_id}",
            data=json.dumps(
                {
                    "success": True,
                    "message": "",
                    "failures": {
                        "files": {"missing": [], "changed": [], "untracked": []}
                    },
                    "timestamp": None,
                    "started": start_time,
                    "finished": start_time,
                }
            ),
            headers={"Content-Type": "application/json"},
        ),
    ]


@mock.patch(
    "requests.get",
)
@mock.patch(
    "requests.post",
    side_effect=[
        mock.Mock(
            status_code=404,
            spec=requests.Response,
            side_effect=reporting.ReportServiceException,
        ),
        mock.Mock(
            status_code=500,
            spec=requests.Response,
            side_effect=reporting.ReportServiceException,
        ),
    ],
)
def test_scan_handles_exceptions_if_report_url_exists(
    _post, _get, capsys, mock_check_fixity
):
    _get.side_effect = mock_check_fixity
    aip_id = uuid.uuid4()

    response = fixity.scan(
        aip=str(aip_id),
        ss_url=STORAGE_SERVICE_URL,
        ss_user=STORAGE_SERVICE_USER,
        ss_key=STORAGE_SERVICE_KEY,
        session=SESSION,
        report_url=REPORT_URL,
    )

    assert response is True

    captured = capsys.readouterr()
    assert captured.err.strip() == "\n".join(
        [
            f"Unable to POST pre-scan report to {REPORT_URL}",
            f"Fixity scan succeeded for AIP: {aip_id}",
            f"Unable to POST report for AIP {aip_id} to remote service",
        ]
    )


@mock.patch(
    "requests.get",
    side_effect=[
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {},
            },
            spec=requests.Response,
        ),
        mock.Mock(
            **{
                "status_code": 500,
                "json.return_value": {},
            },
            spec=requests.Response,
        ),
    ],
)
def test_scan_handles_exceptions(_get, capsys):
    aip_id = uuid.uuid4()

    response = fixity.scan(
        aip=str(aip_id),
        ss_url=STORAGE_SERVICE_URL,
        ss_user=STORAGE_SERVICE_USER,
        ss_key=STORAGE_SERVICE_KEY,
        session=SESSION,
    )

    assert response is None

    captured = capsys.readouterr()
    assert (
        f'Storage service at "{STORAGE_SERVICE_URL}" encountered an internal error while scanning AIP {aip_id}\n'
        == captured.err
    )


@mock.patch(
    "requests.get",
    side_effect=[
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {},
            },
            spec=requests.Response,
        ),
        mock.Mock(
            **{
                "json.return_value": {},
            },
            spec=requests.Response,
            side_effect=ConnectionError,
        ),
    ],
)
def test_scan_handles_exceptions_if_no_scan_attempted(_get):
    aip_id = uuid.uuid4()

    response = fixity.scan(
        aip=str(aip_id),
        ss_url=STORAGE_SERVICE_URL,
        ss_user=STORAGE_SERVICE_USER,
        ss_key=STORAGE_SERVICE_KEY,
        session=SESSION,
    )

    assert response is None
    assert Report(aip_id=aip_id).success is None


@pytest.mark.parametrize(
    "status, error_message",
    [
        (True, "succeeded"),
        (False, "failed"),
        (None, "didn't run"),
    ],
    ids=["Success", "Fail", "Did not run"],
)
def test_scan_message(status, error_message):
    aip_id = uuid.uuid4()

    response = fixity.scan_message(
        aip_uuid=aip_id, status=status, message=error_message
    )

    assert (
        response == f"Fixity scan {error_message} for AIP: {aip_id} ({error_message})"
    )


@mock.patch(
    "requests.get",
)
def test_scanall(_get, capsys, mock_check_fixity):
    aip1_uuid = "41e12f76-354e-402d-85ee-f812cb72f6e6"
    aip2_uuid = "807ecfb7-08b1-4435-87ec-5c6bfbe62225"
    _get.side_effect = [
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {
                    "meta": {"next": None},
                    "objects": [
                        {
                            "package_type": "AIP",
                            "status": "UPLOADED",
                            "uuid": aip1_uuid,
                        },
                        {
                            "package_type": "AIP",
                            "status": "UPLOADED",
                            "uuid": aip2_uuid,
                        },
                    ],
                },
            },
            spec=requests.Response,
        ),
        *mock_check_fixity,
        *mock_check_fixity,
    ]

    response = fixity.scanall(
        ss_url=STORAGE_SERVICE_URL,
        ss_user=STORAGE_SERVICE_USER,
        ss_key=STORAGE_SERVICE_KEY,
        session=SESSION,
    )

    assert response is True

    captured = capsys.readouterr()
    expected_output = "\n".join(
        [
            f"Fixity scan succeeded for AIP: {aip1_uuid}",
            f"Fixity scan succeeded for AIP: {aip2_uuid}",
            "Successfully scanned 2 AIPs",
        ]
    )
    assert captured.err.strip() == expected_output


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
                            "uuid": "77adb748-8d9c-47ec-b593-53465749ce0e",
                        },
                        {
                            "package_type": "AIP",
                            "status": "UPLOADED",
                            "uuid": "32f62f8b-ecfd-419e-a3e9-911ec23d0573",
                        },
                    ],
                },
            },
            spec=requests.Response,
        ),
        mock.Mock(
            **{
                "status_code": 401,
                "json.return_value": {},
            },
            spec=requests.Response,
            side_effect=Exception,
        ),
        mock_scan_aip,
        mock.Mock(
            **{
                "status_code": 401,
                "json.return_value": {},
            },
            spec=requests.Response,
            side_effect=Exception,
        ),
        mock_scan_aip,
    ],
)
def test_scanall_handles_exceptions(_get, capsys):
    response = fixity.scanall(
        ss_url=STORAGE_SERVICE_URL,
        ss_user=STORAGE_SERVICE_USER,
        ss_key=STORAGE_SERVICE_KEY,
        session=SESSION,
    )

    assert response is False

    captured = capsys.readouterr()
    assert (
        "Internal error encountered while scanning AIP 77adb748-8d9c-47ec-b593-53465749ce0e (StorageServiceError)\n"
        in captured.out
    )


@mock.patch("requests.get")
@mock.patch.object(fixity, "Session", lambda: SESSION)
def test_main_scan(_get, monkeypatch, mock_check_fixity, capsys):
    _get.side_effect = mock_check_fixity
    monkeypatch.setenv("STORAGE_SERVICE_URL", STORAGE_SERVICE_URL)
    monkeypatch.setenv("STORAGE_SERVICE_USER", STORAGE_SERVICE_USER)
    monkeypatch.setenv("STORAGE_SERVICE_KEY", STORAGE_SERVICE_KEY)
    aip_id = str(uuid.uuid4())
    sys.argv = ["fixity.py", "scan", aip_id]

    result = fixity.main()

    assert result == 0

    captured = capsys.readouterr()
    assert captured.err.strip() == f"Fixity scan succeeded for AIP: {aip_id}"


@mock.patch("requests.get")
@mock.patch.object(fixity, "Session", lambda: SESSION)
def test_main_handles_exceptions_if_scanall_fails(_get, monkeypatch, capsys):
    aip_id = str(uuid.uuid4())
    _get.side_effect = [
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {
                    "meta": {"next": None},
                    "objects": [
                        {
                            "package_type": "AIP",
                            "status": "UPLOADED",
                            "uuid": f"{aip_id}",
                        },
                        {
                            "package_type": "AIP",
                            "status": "UPLOADED",
                            "uuid": "32f62f8b-ecfd-419e-a3e9-911ec23d0573",
                        },
                    ],
                },
            },
            spec=requests.Response,
        ),
        mock.Mock(
            **{
                "status_code": 401,
                "json.return_value": {},
            },
            spec=requests.Response,
            side_effect=Exception,
        ),
        mock_scan_aip,
        mock.Mock(
            **{
                "status_code": 401,
                "json.return_value": {},
            },
            spec=requests.Response,
            side_effect=Exception,
        ),
        mock_scan_aip,
    ]

    monkeypatch.setenv("STORAGE_SERVICE_URL", STORAGE_SERVICE_URL)
    monkeypatch.setenv("STORAGE_SERVICE_USER", STORAGE_SERVICE_USER)
    monkeypatch.setenv("STORAGE_SERVICE_KEY", STORAGE_SERVICE_KEY)
    sys.argv = ["fixity.py", "scanall"]

    result = fixity.main()

    assert result == 1

    captured = capsys.readouterr()
    assert (
        captured.out.strip()
        == f"Internal error encountered while scanning AIP {aip_id} (StorageServiceError)"
    )
