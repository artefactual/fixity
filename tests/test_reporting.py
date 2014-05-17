from fixity.models import AIP, Report
from fixity import reporting
from fixity.utils import InvalidUUID

import pytest
import vcr

import os
from datetime import datetime


REPORT_URL = "http://localhost:8003/"


def json_string(filename):
    path = os.path.normpath(os.path.join(__file__, "..", "..", "fixtures", "json", filename))
    with open(path) as jsonfile:
        return jsonfile.read()


@vcr.use_cassette('fixtures/vcr_cassettes/post_failed_report.yaml')
def test_posting_report():
    json_report = json_string("test_failed_report.json")
    aip = AIP(
        uuid="ed42aadc-d854-46c6-b455-cd384eef1618"
    )
    report = Report(
        aip=aip,
        begun=datetime.fromtimestamp(1400022946),
        ended=datetime.fromtimestamp(1400023208),
        success=False,
        posted=False,
        report=json_report
    )
    reporting.post_report(aip.uuid, report, REPORT_URL)


def test_posting_report_raises_on_invalid_uuid():
    with pytest.raises(InvalidUUID):
        reporting.post_report("foo", None, None)
