import os
from datetime import datetime
from unittest import mock

import pytest
import requests

from fixity import reporting
from fixity.models import AIP
from fixity.models import Report
from fixity.utils import InvalidUUID

REPORT_URL = "http://localhost:8003/"


def json_string(filename: str) -> str:
    path = os.path.normpath(
        os.path.join(__file__, "..", "..", "fixtures", "json", filename)
    )
    with open(path) as jsonfile:
        return jsonfile.read()


@mock.patch(
    "requests.post", side_effect=[mock.Mock(status_code=201, spec=requests.Response)]
)
def test_posting_prescan_report(_post: mock.Mock) -> None:
    aip = "be1074fe-217b-46e0-afec-400ea1a2eb36"
    start_time = datetime.fromtimestamp(1400022946)
    result = reporting.post_pre_scan_report(aip, start_time, REPORT_URL)
    assert result is True


def test_posting_prescan_report_raises_on_invalid_uuid() -> None:
    with pytest.raises(InvalidUUID):
        reporting.post_pre_scan_report("foo", None, None)


@mock.patch(
    "requests.post", side_effect=[mock.Mock(status_code=500, spec=requests.Response)]
)
def test_posting_prescan_report_raises_on_500(_post: mock.Mock) -> None:
    with pytest.raises(reporting.ReportServiceException):
        aip = "90cf0850-f5d2-4023-95e2-0e2b7a1e1b8e"
        start_time = datetime.fromtimestamp(1400022946)
        reporting.post_pre_scan_report(aip, start_time, REPORT_URL)


@mock.patch(
    "requests.post", side_effect=[mock.Mock(status_code=404, spec=requests.Response)]
)
def test_posting_prescan_report_raises_on_404(_post: mock.Mock) -> None:
    with pytest.raises(reporting.ReportServiceException):
        aip = "90cf0850-f5d2-4023-95e2-0e2b7a1e1b8e"
        start_time = datetime.fromtimestamp(1400022946)
        reporting.post_pre_scan_report(aip, start_time, REPORT_URL)


def test_posting_prescan_report_raises_when_unable_to_connect() -> None:
    with pytest.raises(reporting.ReportServiceException):
        aip = "90cf0850-f5d2-4023-95e2-0e2b7a1e1b8e"
        start_time = datetime.fromtimestamp(1400022946)
        reporting.post_pre_scan_report(aip, start_time, "http://foo")


@mock.patch(
    "requests.post", side_effect=[mock.Mock(status_code=201, spec=requests.Response)]
)
def test_posting_success_report(_post: mock.Mock) -> None:
    json_report = json_string("test_failed_report.json")
    aip = AIP(uuid="ed42aadc-d854-46c6-b455-cd384eef1618")
    report = Report(
        aip=aip,
        begun=datetime.fromtimestamp(1400022946),
        ended=datetime.fromtimestamp(1400023208),
        success=False,
        posted=False,
        report=json_report,
    )
    reporting.post_success_report(aip.uuid, report, REPORT_URL)


def test_posting_success_report_raises_on_invalid_uuid() -> None:
    with pytest.raises(InvalidUUID):
        reporting.post_success_report("foo", None, None)


@mock.patch(
    "requests.post", side_effect=[mock.Mock(status_code=500, spec=requests.Response)]
)
def test_posting_success_report_raises_on_500(_post: mock.Mock) -> None:
    with pytest.raises(reporting.ReportServiceException):
        json_report = json_string("test_failed_report.json")
        aip = AIP(uuid="ed42aadc-d854-46c6-b455-cd384eef1618")
        report = Report(
            aip=aip,
            begun=datetime.fromtimestamp(1400022946),
            ended=datetime.fromtimestamp(1400023208),
            success=False,
            posted=False,
            report=json_report,
        )
        reporting.post_success_report(aip.uuid, report, REPORT_URL)


@mock.patch(
    "requests.post", side_effect=[mock.Mock(status_code=404, spec=requests.Response)]
)
def test_posting_success_report_raises_on_404(_post: mock.Mock) -> None:
    with pytest.raises(reporting.ReportServiceException):
        json_report = json_string("test_failed_report.json")
        aip = AIP(uuid="ed42aadc-d854-46c6-b455-cd384eef1618")
        report = Report(
            aip=aip,
            begun=datetime.fromtimestamp(1400022946),
            ended=datetime.fromtimestamp(1400023208),
            success=False,
            posted=False,
            report=json_report,
        )
        reporting.post_success_report(aip.uuid, report, REPORT_URL)


def test_posting_success_report_raises_when_unable_to_connect() -> None:
    with pytest.raises(reporting.ReportServiceException):
        json_report = json_string("test_failed_report.json")
        aip = AIP(uuid="ed42aadc-d854-46c6-b455-cd384eef1618")
        report = Report(
            aip=aip,
            begun=datetime.fromtimestamp(1400022946),
            ended=datetime.fromtimestamp(1400023208),
            success=False,
            posted=False,
            report=json_report,
        )
        reporting.post_success_report(aip.uuid, report, "http://foo")


def test_posting_success_report_posted_is_false_on_raise() -> None:
    try:
        json_report = json_string("test_failed_report.json")
        aip = AIP(uuid="ed42aadc-d854-46c6-b455-cd384eef1618")
        report = Report(
            aip=aip,
            begun=datetime.fromtimestamp(1400022946),
            ended=datetime.fromtimestamp(1400023208),
            success=False,
            posted=True,
            report=json_report,
        )
        reporting.post_success_report(aip.uuid, report, "http://foo")
    except reporting.ReportServiceException:
        pass

    assert report.posted is False


def test_posting_success_report_success_none() -> None:
    json_report = json_string("test_failed_report.json")
    aip = AIP(uuid="ed42aadc-d854-46c6-b455-cd384eef1618")
    report = Report(
        aip=aip,
        begun=datetime.fromtimestamp(1400022946),
        ended=datetime.fromtimestamp(1400023208),
        success=None,
        posted=False,
        report=json_report,
    )
    assert reporting.post_success_report(aip.uuid, report, REPORT_URL) is None
