from datetime import datetime
import httplib
import json
import urllib

from sqlalchemy.orm.exc import NoResultFound

from models import AIP, Report, Session
from utils import check_valid_uuid


class StorageServiceError(Exception):
    pass


def get_all_aips(connection):
    """
    Returns a list of all AIPs stored in a storage service installation.
    Each AIP in the list is a dict as returned by the storage
    service API.

    connection is a active httplib.HTTPConnection instance pointing to
    a storage service installation.
    """

    if not isinstance(connection, httplib.HTTPConnection):
        raise TypeError('connection must be an active HTTPConnection to the storage service')

    connection.request('GET', '/api/v2/file/')
    response = connection.getresponse()
    if response.status == 404:
        raise StorageServiceError('Storage service at \"{}\" returned 404'.format(connection.host))
    results = json.load(response)
    limit = results['meta']['limit']
    count = results['meta']['limit']
    aips = [aip for aip in results['objects'] if aip['package_type'] == 'AIP']

    while count < results['meta']['total_count']:
        params = urllib.urlencode({'count': count + limit})
        connection.request('GET', '/api/v2/file/', params)

        response = connection.getresponse()
        results = json.load(response)
        count += limit

        aips.extend([aip['uuid'] for aip in results['objects'] if aip['package_type'] == 'AIP'])

    return aips


def get_single_aip(uuid, connection):
    """
    Fetch detailed information on an AIP from the storage service.

    Given an AIP UUID, fetches a dict with full information on the AIP
    from the storage service.
    """
    check_valid_uuid(uuid)  # raises if not a valid UUID
    connection.request('GET', '/api/v2/file/' + uuid + '/')
    response = connection.getresponse()
    if response.status == 404:
        raise StorageServiceError('Storage service at \"{}\" returned 404'.format(connection.host))
    return json.load(response)


def create_report(aip, success, begun, ended, report_string):
    return Report(
        aip=aip,
        begun=None,
        ended=None,
        success=success,
        report=report_string
    )


def scan_aip(aip_uuid, connection):
    """
    Scans fixity for the given AIP.

    The first argument should either be an AIP UUID, as a string,
    or an AIP model instance. If no AIP with the given UUID is
    present in the database, a new object is created.

    A tuple of (success, report) is returned.

    success is a trilean that returns True or False for success or failure,
    and None if the scan could not begin.

    report is a dict containing the parsed JSON report from the storage
    service.

    If the storage service returns a 404, raises a StorageServiceError.
    A report is still saved to the database in this case.
    """
    session = Session()
    if not isinstance(connection, httplib.HTTPConnection):
        raise TypeError('connection must be an active HTTPConnection to the storage service')
    if isinstance(aip_uuid, AIP):
        aip = aip_uuid
    else:
        check_valid_uuid(aip_uuid)
        try:
            aip = session.query(AIP).filter_by(uuid=aip_uuid).one()
        except NoResultFound:
            aip = AIP(uuid=aip_uuid)
            session.commit()

    begun = datetime.now()
    connection.request('GET', '/api/v2/file/' + aip.uuid + '/scan_fixity/')
    response = connection.getresponse()
    ended = datetime.now()

    # Typically occurs if the storage service is unable to find the
    # requested AIP, or if the requested API call is not available.
    if response.status == 404:
        create_report(aip, None, begun, ended, '{"success": null, "message": "Storage service returned 404"}')
        session.commit()
        raise StorageServiceError('A fixity scan could not be started for the AIP with uuid \"{}\"'.format(aip.uuid))

    report_string = json.read()
    report = json.loads(report_string)
    success = report.get('success', None)

    create_report(aip, success, begun, ended, report_string)
    session.commit()

    return (success, report)
