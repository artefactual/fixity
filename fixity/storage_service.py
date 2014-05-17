from datetime import datetime
import json
import time

import requests
from sqlalchemy.orm.exc import NoResultFound

from models import AIP, Report, Session
from utils import check_valid_uuid


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


class InvalidUUID(Exception):
    def __init__(self, uuid):
        self.message = "Invalid UUID: {}".format(uuid)

    def __str__(self):
        return self.message


def get_all_aips(ss_url):
    """
    Returns a list of all AIPs stored in a storage service installation.
    Each AIP in the list is a dict as returned by the storage
    service API.
    """

    url = ss_url + 'api/v2/file/'
    try:
        response = requests.get(url)
    except requests.ConnectionError:
        raise StorageServiceError(UNABLE_TO_CONNECT_ERROR.format(ss_url))

    if response.status_code == 404:
        raise StorageServiceError('Storage service at \"{}\" returned 404'.format(ss_url))
    if response.status_code == 500:
        raise StorageServiceError('Storage service at \"{}\" encountered an internal error while requesting AIPs'.format(ss_url))
    results = response.json()
    limit = results['meta']['limit']
    count = results['meta']['limit']
    aips = [aip for aip in results['objects'] if aip['package_type'] == 'AIP']

    while count < results['meta']['total_count']:
        params = {'count': str(count + limit)}
        response = requests.get(url, params=params)

        results = response.json()
        count += limit

        aips.extend([aip['uuid'] for aip in results['objects'] if aip['package_type'] == 'AIP'])

    return aips


def get_single_aip(uuid, ss_url):
    """
    Fetch detailed information on an AIP from the storage service.

    Given an AIP UUID, fetches a dict with full information on the AIP
    from the storage service.
    """
    try:
        check_valid_uuid(uuid)
    except ValueError:
        raise InvalidUUID(uuid)

    try:
        response = requests.get(ss_url + 'api/v2/file/' + uuid + '/')
    except requests.ConnectionError:
        raise(StorageServiceError(UNABLE_TO_CONNECT_ERROR.format(ss_url)))

    if response.status_code == 404:
        raise StorageServiceError('Storage service at \"{}\" returned 404'.format(ss_url))
    if response.status_code == 500:
        raise StorageServiceError('Storage service at \"{}\" encountered an internal error while requesting aip'.format(ss_url, uuid))
    return response.json()


def create_report(aip, success, begun, ended, report_string):
    return Report(
        aip=aip,
        begun=None,
        ended=None,
        success=success,
        report=report_string
    )


def scan_aip(aip_uuid, ss_url):
    """
    Scans fixity for the given AIP.

    The first argument should either be an AIP UUID, as a string,
    or an AIP model instance. If no AIP with the given UUID is
    present in the database, a new object is created.

    A tuple of (success, report) is returned.

    success is a trilean that returns True or False for success or failure,
    and None if the scan could not begin.

    report is a Report model object, which typically has already been committed
    to the database.

    If the storage service returns a 404, raises a StorageServiceError.
    A report is still saved to the database in this case.
    """
    session = Session()
    if isinstance(aip_uuid, AIP):
        aip = aip_uuid
    else:
        try:
            check_valid_uuid(aip_uuid)
        except ValueError:
            raise InvalidUUID(aip_uuid)

        try:
            aip = session.query(AIP).filter_by(uuid=aip_uuid).one()
        except NoResultFound:
            aip = AIP(uuid=aip_uuid)
            session.add(aip)

    begun = datetime.utcnow()
    try:
        response = requests.get(ss_url + 'api/v2/file/' + aip.uuid + '/check_fixity/')
    except requests.ConnectionError:
        raise StorageServiceError(UNABLE_TO_CONNECT_ERROR.format(ss_url))
    ended = datetime.utcnow()

    report = response.json()
    report["started"] = int(time.mktime(begun.utctimetuple()))
    report["finished"] = int(time.mktime(ended.utctimetuple()))
    if not "success" in report:
        report["success"] = None

    # Typically occurs if the storage service is unable to find the
    # requested AIP, or if the requested API call is not available.
    if response.status_code == 404:
        report = create_report(aip, None, begun, ended, '{"success": null, "message": "Storage service returned 404"}')
        session.add(report)
        session.commit()
        raise StorageServiceError(
            'A fixity scan could not be started for the AIP with uuid \"{}\"'.format(aip.uuid),
            report=report
        )
    if response.status_code == 500:
        report = create_report(aip, None, begun, ended, '{"success": null, "message": "Storage service returned 500"}')
        session.add(report)
        session.commit()
        raise StorageServiceError(
            'Storage service at \"{}\" encountered an internal error while scanning AIP {}'.format(ss_url, aip.uuid),
            report=report
        )

    success = report.get('success', None)
    report_string = json.dumps(report)

    report_object = create_report(aip, success, begun, ended, report_string)
    session.add(report_object)
    session.commit()

    return (success, report_object)