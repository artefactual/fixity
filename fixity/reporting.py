import calendar
import json

from .utils import check_valid_uuid

import requests


class ReportServiceException(Exception):
    pass


def post_pre_scan_report(aip, start_time, report_url, report_auth=(), session_id=None):
    """
    Post a pre-scan report to a remote system.

    This report will contain no information beyond start time and,
    if provided, a session_id. It is used to notify a reporting system
    that a scan is beginning, and to expect a completion report at
    some time in the future.

    start_time is a datetime object representing the time the scan begun.
    For information on other parameters, see post_success_report.

    report_auth is a tuple of (username, pass)
    """

    check_valid_uuid(aip)

    report = {"started": int(calendar.timegm(start_time.utctimetuple()))}
    if session_id:
        report["session_uuid"] = session_id
    body = json.dumps(report)

    kwargs = {
        "data": body,
        "headers": {
            "Content-Type": "application/json"
        }
    }
    if report_auth:
        kwargs["auth"] = report_auth

    url = report_url + 'api/fixity/{}'.format(aip)

    try:
        response = requests.post(url, **kwargs)
    except requests.ConnectionError:
        raise ReportServiceException("Unable to connect to report service at URL {}".format(report_url))

    if not response.status_code == 201:
        raise ReportServiceException("Report service returned {}".format(response.status_code))

    return True


def post_success_report(aip, report, report_url, report_auth=(), session_id=None):
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
    if report and report.success is None:
        return None
    check_valid_uuid(aip)

    body = report.report

    if session_id:
        parsed_report = json.loads(body)
        parsed_report["session_uuid"] = session_id
        body = json.dumps(parsed_report)

    kwargs = {
        "data": body,
        "headers": {
            "Content-Type": "application/json"
        }
    }
    if report_auth:
        kwargs["auth"] = report_auth

    url = report_url + 'api/fixity/{}'.format(aip)

    try:
        response = requests.post(url, **kwargs)
    except requests.ConnectionError:
        report.posted = False
        raise ReportServiceException("Unable to connect to report service at URL {}".format(report_url))

    if not response.status_code == 201:
        report.posted = False
    else:
        report.posted = True

    if response.status_code == 500:
        raise ReportServiceException("Report service encountered an internal error when attempting to POST report for AIP {}".format(aip))
    elif response.status_code != 201:
        raise ReportServiceException("Report service returned {} when attempting to POST report for AIP {}".format(response.status_code, aip))

    return report.posted
