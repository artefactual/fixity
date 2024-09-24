import io
import json
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
def environment(monkeypatch):
    monkeypatch.setenv("STORAGE_SERVICE_URL", STORAGE_SERVICE_URL)
    monkeypatch.setenv("STORAGE_SERVICE_USER", STORAGE_SERVICE_USER)
    monkeypatch.setenv("STORAGE_SERVICE_KEY", STORAGE_SERVICE_KEY)


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


def _assert_stream_content_matches(stream, expected):
    stream.seek(0)
    assert [line.strip() for line in stream.readlines()] == expected


@mock.patch("requests.get")
def test_scan(_get, environment, mock_check_fixity):
    _get.side_effect = mock_check_fixity
    aip_id = uuid.uuid4()
    stream = io.StringIO()

    response = fixity.main(["scan", str(aip_id)], stream=stream)

    assert response == 0

    _assert_stream_content_matches(stream, [f"Fixity scan succeeded for AIP: {aip_id}"])

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


@mock.patch("time.time")
@mock.patch("requests.get")
def test_scan_if_timestamps_argument_is_passed(
    _get, time, environment, mock_check_fixity
):
    _get.side_effect = mock_check_fixity
    aip_id = uuid.uuid4()
    timestamp = 1514775600
    time.return_value = timestamp
    stream = io.StringIO()

    response = fixity.main(["scan", str(aip_id), "--timestamps"], stream=stream)

    assert response == 0

    _assert_stream_content_matches(
        stream,
        [f"[2018-01-01 03:00:00 UTC] Fixity scan succeeded for AIP: {aip_id}"],
    )

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


@mock.patch("fixity.fixity.uuid4")
@mock.patch("fixity.utils.utcnow")
@mock.patch("requests.get")
@mock.patch(
    "requests.post",
    side_effect=[
        mock.Mock(status_code=201, spec=requests.Response),
        mock.Mock(status_code=201, spec=requests.Response),
    ],
)
def test_scan_if_report_url_exists(
    _post, _get, utcnow, uuid4, mock_check_fixity, environment, monkeypatch
):
    uuid4.return_value = expected_uuid = uuid.uuid4()
    _get.side_effect = mock_check_fixity
    monkeypatch.setenv("REPORT_URL", REPORT_URL)
    start_time = 1514775600
    utcnow.return_value = datetime.fromtimestamp(start_time, timezone.utc)
    aip_id = uuid.uuid4()
    stream = io.StringIO()

    response = fixity.main(["scan", str(aip_id)], stream=stream)

    assert response == 0

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
            data=json.dumps(
                {"started": start_time, "session_uuid": str(expected_uuid)}
            ),
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
                    "session_uuid": str(expected_uuid),
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
    _post, _get, environment, monkeypatch, mock_check_fixity
):
    _get.side_effect = mock_check_fixity
    aip_id = uuid.uuid4()
    stream = io.StringIO()
    monkeypatch.setenv("REPORT_URL", REPORT_URL)

    response = fixity.main(["scan", str(aip_id)], stream=stream)

    assert response == 0

    _assert_stream_content_matches(
        stream,
        [
            f"Unable to POST pre-scan report to {REPORT_URL}",
            f"Fixity scan succeeded for AIP: {aip_id}",
            f"Unable to POST report for AIP {aip_id} to remote service",
        ],
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
def test_scan_handles_exceptions(_get, environment):
    aip_id = uuid.uuid4()
    stream = io.StringIO()

    response = fixity.main(["scan", str(aip_id)], stream=stream)

    assert response is None

    _assert_stream_content_matches(
        stream,
        [
            f'Storage service at "{STORAGE_SERVICE_URL}" encountered an internal error while scanning AIP {aip_id}'
        ],
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
def test_scan_handles_exceptions_if_no_scan_attempted(_get, environment):
    aip_id = uuid.uuid4()

    response = fixity.main(["scan", str(aip_id)])

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
def test_scanall(_get, environment, mock_check_fixity):
    aip1_uuid = str(uuid.uuid4())
    aip2_uuid = str(uuid.uuid4())
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
    stream = io.StringIO()

    response = fixity.main(["scanall"], stream=stream)

    assert response == 0

    _assert_stream_content_matches(
        stream,
        [
            f"Fixity scan succeeded for AIP: {aip1_uuid}",
            f"Fixity scan succeeded for AIP: {aip2_uuid}",
            "Successfully scanned 2 AIPs",
        ],
    )


@mock.patch("requests.get")
def test_scanall_handles_exceptions(_get, environment):
    aip_id1 = str(uuid.uuid4())
    aip_id2 = str(uuid.uuid4())
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
                            "uuid": f"{aip_id1}",
                        },
                        {
                            "package_type": "AIP",
                            "status": "UPLOADED",
                            "uuid": f"{aip_id2}",
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
    stream = io.StringIO()

    response = fixity.main(["scanall"], stream=stream)

    assert response == 1

    _assert_stream_content_matches(
        stream,
        [
            f"Internal error encountered while scanning AIP {aip_id1} (StorageServiceError)",
            f'Storage service at "{STORAGE_SERVICE_URL}" failed authentication while scanning AIP {aip_id2}',
            "Successfully scanned 2 AIPs",
        ],
    )


@mock.patch("requests.get")
def test_main_handles_exceptions_if_scanall_fails(_get, environment):
    aip_id1 = str(uuid.uuid4())
    aip_id2 = str(uuid.uuid4())
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
                            "uuid": f"{aip_id1}",
                        },
                        {
                            "package_type": "AIP",
                            "status": "UPLOADED",
                            "uuid": f"{aip_id2}",
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
    stream = io.StringIO()

    result = fixity.main(["scanall"], stream=stream)

    assert result == 1

    _assert_stream_content_matches(
        stream,
        [
            f"Internal error encountered while scanning AIP {aip_id1} (StorageServiceError)",
            f'Storage service at "{STORAGE_SERVICE_URL}" failed authentication while scanning AIP {aip_id2}',
            "Successfully scanned 2 AIPs",
        ],
    )


@mock.patch("requests.get")
def test_scanall_if_sort_argument_is_passed(_get, environment, mock_check_fixity):
    aip1_uuid = str(uuid.uuid4())
    aip2_uuid = str(uuid.uuid4())
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

    stream = io.StringIO()

    response = fixity.main(["scanall", "--sort"], stream=stream)

    assert response == 0

    _assert_stream_content_matches(
        stream,
        [
            f"Fixity scan succeeded for AIP: {aip1_uuid}",
            f"Fixity scan succeeded for AIP: {aip2_uuid}",
            "Successfully scanned 2 AIPs",
        ],
    )

    assert _get.mock_calls == [
        mock.call(
            f"{STORAGE_SERVICE_URL}api/v2/file/",
            params={"username": "test", "api_key": "test"},
        ),
        mock.call(
            f"{STORAGE_SERVICE_URL}api/v2/file/{aip1_uuid}/",
            params={"username": STORAGE_SERVICE_USER, "api_key": STORAGE_SERVICE_KEY},
        ),
        mock.call(
            f"{STORAGE_SERVICE_URL}api/v2/file/{aip1_uuid}/check_fixity/",
            params={"username": STORAGE_SERVICE_USER, "api_key": STORAGE_SERVICE_KEY},
        ),
        mock.call(
            f"{STORAGE_SERVICE_URL}api/v2/file/{aip2_uuid}/",
            params={"username": STORAGE_SERVICE_USER, "api_key": STORAGE_SERVICE_KEY},
        ),
        mock.call(
            f"{STORAGE_SERVICE_URL}api/v2/file/{aip2_uuid}/check_fixity/",
            params={"username": STORAGE_SERVICE_USER, "api_key": STORAGE_SERVICE_KEY},
        ),
    ]
