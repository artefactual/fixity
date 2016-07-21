import calendar
from datetime import datetime
import json

import requests
from sqlalchemy.orm.exc import NoResultFound

from .models import AIP, Report
from .utils import check_valid_uuid


UNABLE_TO_CONNECT_ERROR = "Unable to connect to storage service instance at {} (is it running?)"


class StorageServiceError(Exception):
    """
    Subclass of Exception used to report errors from the storage service.

    The report keyword argument should be used to pass in a JSON report from
    functions that scan the storage service in the case that the function
    itself will not return, but the caller still needs access to it.
    """

    def __init__(self, message, report=None):
        self.report = report
        super(StorageServiceError, self).__init__(message)


def _get_aips(ss_url, ss_user, ss_key, uri='api/v2/file/'):
    url = ss_url + uri
    params = {'username': ss_user, 'api_key': ss_key}
    try:
        response = requests.get(url, params=params)
    except requests.ConnectionError:
        raise StorageServiceError(UNABLE_TO_CONNECT_ERROR.format(ss_url))

    if response.status_code == 500:
        raise StorageServiceError('Storage service at "{}" encountered an internal error while requesting AIPs'.format(ss_url))
    elif response.status_code == 504:
        raise StorageServiceError('Storage service at "{}" encountered a gateway timeout while requesting AIPs'.format(ss_url))
    elif response.status_code == 401:
        raise StorageServiceError('Storage service at "{}" failed authentication while requesting AIPs'.format(ss_url))
    elif response.status_code != 200:
        raise StorageServiceError('Storage service at "{}" returned {} while requesting AIPs'.format(ss_url, response.status_code))

    results = response.json()
    filtered_aips = [aip for aip in results['objects'] if aip['package_type'] == 'AIP' and aip['status'] == u"UPLOADED"]
    results["objects"] = filtered_aips
    return results


def get_all_aips(ss_url, ss_user, ss_key):
    """
    Returns a list of all AIPs stored in a storage service installation.
    Each AIP in the list is a dict as returned by the storage
    service API.
    """

    results = _get_aips(ss_url, ss_user, ss_key)
    aips = results["objects"]

    # The "next" key contains a prebuilt URL with query
    # parameters to the next set of items; use that to keep
    # iterating until we hit the end of the available AIPs.
    while results["meta"]["next"] is not None:
        results = _get_aips(ss_url, ss_user, ss_key, uri=results["meta"]["next"][1:])
        aips.extend(results["objects"])

    return aips


def get_single_aip(uuid, ss_url, ss_user, ss_key):
    """
    Fetch detailed information on an AIP from the storage service.

    Given an AIP UUID, fetches a dict with full information on the AIP
    from the storage service.
    """
    check_valid_uuid(uuid)

    params = {'username': ss_user, 'api_key': ss_key}
    try:
        response = requests.get(ss_url + 'api/v2/file/' + uuid + '/', params=params)
    except requests.ConnectionError:
        raise(StorageServiceError(UNABLE_TO_CONNECT_ERROR.format(ss_url)))

    if response.status_code == 500:
        raise StorageServiceError('Storage service at "{}" encountered an internal error while requesting AIP with UUID {}'.format(ss_url, uuid))
    elif response.status_code == 504:
        raise StorageServiceError('Storage service at "{}" encounterd a gateway timeout while requesting AIP with UUID {}'.format(ss_url, uuid))
    elif response.status_code == 401:
        raise StorageServiceError('Storage service at "{}" failed authentication while requesting AIP with UUID {}'.format(ss_url, uuid))
    if response.status_code != 200:
        raise StorageServiceError('Storage service at "{}" returned {} while requesting AIP with UUID {}'.format(ss_url, response.status_code, uuid))
    return response.json()


def create_report(aip, success, begun, ended, report_string):
    return Report(
        aip=aip,
        begun=begun,
        ended=ended,
        success=success,
        report=report_string
    )


def scan_aip(aip_uuid, ss_url, ss_user, ss_key, session, start_time=None, force_local=False):
    """
    Scans fixity for the given AIP.

    The first argument should either be an AIP UUID, as a string,
    or an AIP model instance. If no AIP with the given UUID is
    present in the database, a new object is created.

    The second argument is the URL prefix to the storage service instance
    to use, such as "http://localhost:8000/". It must end with a /.

    session is an instance of models.Session, which will be used to query
    for AIPs in the database.

    start_time, if passed, should be a datetime object representing the
    time at which the scan began. If not provided, the start time will
    be calculated immediately before the scan begins. This should be
    passed in the case that a pre-scan report will be POSTed to a server,
    in which case both reports should have the identical time.

    force_local, if True, will request the Storage Service to perform a local
    fixity check, instead of using the Space's fixity (if available).

    A tuple of (success, report) is returned.

    success is a trilean that returns True or False for success or failure,
    and None if the scan could not begin.

    report is a Report model object.

    If the storage service returns a 404, raises a StorageServiceError.
    A report is still saved to the database in this case.
    """
    if isinstance(aip_uuid, AIP):
        aip = aip_uuid
    else:
        check_valid_uuid(aip_uuid)

        try:
            aip = session.query(AIP).filter_by(uuid=aip_uuid).one()
        except NoResultFound:
            aip = AIP(uuid=aip_uuid)

    if not start_time:
        begun = datetime.utcnow()
    else:
        begun = start_time

    params = {'username': ss_user, 'api_key': ss_key}
    if force_local:
        params = {'username': ss_user, 'api_key': ss_key, 'force_local': force_local}
    try:
        response = requests.get(ss_url + 'api/v2/file/' + aip.uuid + '/check_fixity/', params=params)
    except requests.ConnectionError:
        raise StorageServiceError(UNABLE_TO_CONNECT_ERROR.format(ss_url))
    ended = datetime.utcnow()

    begun_int = int(calendar.timegm(begun.utctimetuple()))
    ended_int = int(calendar.timegm(ended.utctimetuple()))

    # Typically occurs if the storage service is unable to find the
    # requested AIP, or if the requested API call is not available.
    if response.status_code == 404:
        json_report = {
            "success": None,
            "message": "Storage service returned 404",
            "started": begun_int,
            "finished": ended_int
        }
        report = create_report(aip, None, begun, ended, json.dumps(json_report))
        raise StorageServiceError(
            'A fixity scan could not be started for the AIP with uuid \"{}\"'.format(aip.uuid),
            report=report
        )
    if response.status_code == 500:
        json_report = {
            "success": None,
            "message": "Storage service returned 500",
            "started": begun_int,
            "finished": ended_int
        }
        report = create_report(aip, None, begun, ended, json.dumps(json_report))
        raise StorageServiceError(
            'Storage service at \"{}\" encountered an internal error while scanning AIP {}'.format(ss_url, aip.uuid),
            report=report
        )
    if response.status_code == 401:
        json_report = {
            "success": None,
            "message": "Storage service returned 401",
            "started": begun_int,
            "finished": ended_int
        }
        report = create_report(aip, None, begun, ended, json.dumps(json_report))
        raise StorageServiceError(
            'Storage service at \"{}\" failed authentication while scanning AIP {}'.format(ss_url, aip.uuid),
            report=report
        )
    if response.status_code != 200:
        json_report = {
            "success": None,
            "message": "Storage service returned {}".format(response.status_code),
            "started": begun_int,
            "finished": ended_int
        }
        report = create_report(aip, None, begun, ended, json.dumps(json_report))
        raise StorageServiceError(
            'Storage service at \"{}\" returned {} while scanning AIP {}'.format(ss_url, response.status_code, aip.uuid),
            report=report
        )

    report = response.json()
    if report.get('timestamp'):
        timestamp = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S")
        timestamp = int(calendar.timegm(timestamp.utctimetuple()))
        report["started"] = timestamp
        report["finished"] = timestamp
    else:
        report["started"] = begun_int
        report["finished"] = ended_int
    if "success" not in report:
        report["success"] = None

    success = report.get('success', None)
    report_string = json.dumps(report)

    report_object = create_report(aip, success, begun, ended, report_string)

    return (success, report_object)
