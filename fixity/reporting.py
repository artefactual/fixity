from models import Session

import requests


def post_report(aip, report, report_url):
    """
    POST a JSON fixity scan report to a remote system.

    aip should be the UUID of an AIP as a string.
    report should be a Report instance.
    report_url should be the base URL for the system to which the request
    will be POSTed.
    """
    body = report.report
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
    else:
        report.posted = True

    session.add(report)
    session.commit()
    return report.posted
