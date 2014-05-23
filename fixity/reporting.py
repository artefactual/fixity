import json

from models import Session
from utils import check_valid_uuid

import requests


class ReportServiceException(Exception):
    pass


def post_success_report(aip, report, report_url, session_id=None):
    """
    POST a JSON fixity scan report to a remote system.

    aip should be the UUID of an AIP as a string.
    report should be a Report instance.
    report_url should be the base URL for the system to which the request
    will be POSTed.

    session_id is an ID string identifying a report session.
    It provides a way to:
      a) Tie together the beginning and end occurrences for the same report,
      b) Tie together multiple reports from the same scan session

    This is an optional parameter, but some reporting services will require it.
    (For instance, the DRMC requires this to be POSTed with every report.)
    """
    check_valid_uuid(aip)

    body = report.report

    if session_id:
        parsed_report = json.loads(body)
        parsed_report["session_uuid"] = session_id
        body = json.dumps(parsed_report)

    headers = {
        "Content-Type": "application/json"
    }
    url = report_url + 'api/fixityreports/{}'.format(aip)

    try:
        response = requests.post(url, data=body, headers=headers)
    except requests.ConnectionError:
        return False

    session = Session()
    if not response.status_code == 201:
        report.posted = False
    elif response.status_code == 404:
        report.posted = False
        session.add(report)
        session.commit()
        raise ReportServiceException("Report service returned 404 when attemptng to POST report for AIP {}".format(aip))
    elif response.status_code == 500:
        report.posted = False
        session.add(report)
        session.commit()
        raise ReportServiceException("Report service encountered an internal error when attempting to POST report for AIP {}".format(aip))
    else:
        report.posted = True

    session.add(report)
    session.commit()
    return report.posted
