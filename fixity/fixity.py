from __future__ import print_function
from argparse import ArgumentParser
from datetime import datetime
import os
import sys
from uuid import uuid4
from time import sleep

from models import AIP, Session
import reporting
import storage_service
from utils import InvalidUUID


class ArgumentError(Exception):
    pass


def store_aips_in_database(aips):
    """
    Add new AIPs to the database from a list of AIP UUID strings.
    """
    session = Session()
    for aip in aips:
        if session.query(AIP.uuid).filter_by(uuid=aip['uuid']).count() == 0:
            session.add(AIP(uuid=aip['uuid']))
    session.commit()


def validate_arguments(args):
    if args.command == 'scan' and not args.aip:
        raise ArgumentError('An AIP UUID must be specified when scanning a single AIP')


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('command')
    parser.add_argument('aip', nargs='?')
    parser.add_argument('--throttle', type=int, default=0)
    args = parser.parse_args()

    validate_arguments(args)
    return args


def fetch_environment_variables(namespace):
    try:
        namespace.ss_url = os.environ['STORAGE_SERVICE_URL']
        if not namespace.ss_url.endswith('/'):
            namespace.ss_url = namespace.ss_url + '/'
        namespace.report_url = os.environ['REPORT_URL']
        if not namespace.report_url.endswith('/'):
            namespace.report_url = namespace.report_url + '/'
    except KeyError:
        raise ArgumentError('Error: A required environment variable was not set')


def scan_message(aip_uuid, status):
    succeeded = "succeeded" if status else "failed"
    return "Fixity scan {} for AIP: {}".format(succeeded, aip_uuid)


def scan(aip, ss_url, report_url=None, session_id=None):
    """
    Instruct the storage service to scan a single AIP.

    This first attempts to query the storage service about the AIP,
    to ensure the storage service still has a record of it, then
    runs a fixity scan.

    aip should be an AIP UUID string.
    ss_url should be the base URL to a storage service installation.
    report_url can be the base URL to a server to which the report will
    be POSTed after the scan completes. If absent, the report will not be
    transmitted.
    """

    # Ensure the storage service knows about this AIP first;
    # get_single_aip() will raise an exception if the storage service
    # does not have an AIP with that UUID, or otherwise errors out
    # while attempting to respond to the request.
    storage_service.get_single_aip(aip, ss_url)

    start_time = datetime.utcnow()

    try:
        reporting.post_pre_scan_report(
            aip, start_time,
            report_url=report_url, session_id=session_id
        )
    except reporting.ReportServiceException:
        print(
            "Unable to POST pre-scan report to {}".format(report_url),
            file=sys.stderr
        )

    try:
        status, report = storage_service.scan_aip(
            aip, ss_url, start_time=start_time
        )
        print(scan_message(aip, status), file=sys.stderr)
    except (storage_service.StorageServiceError, InvalidUUID) as e:
        print(e.message, file=sys.stderr)
        status = None
        if hasattr(e, 'report') and e.report:
            report = e.report
        # Certain classes of exceptions will not return reports because no
        # scan was even attempted; nothing to POST in that case.
        else:
            report = None

    if report_url and report:
        if not reporting.post_success_report(aip, report, report_url, session_id=session_id):
            print("Unable to POST report for AIP {} to remote service".format(aip),
                  file=sys.stderr)

    return status


def scanall(ss_url, report_url=None, throttle_time=0):
    """
    Run a fixity scan on every AIP in a storage service instance.

    ss_url should be the base URL to a storage service installation.
    report_url can be the base URL to a server to which the report will
    be POSTed after the scan completes. If absent, the report will not be
    transmitted.
    """
    success = True

    # The same session ID will be used for every scan,
    # allowing every scan from one run to be identified.
    session_id = str(uuid4())

    try:
        aips = storage_service.get_all_aips(ss_url)
    except storage_service.StorageServiceError as e:
        return e
    count = len(aips)
    for aip in aips:
        scan_success = scan(aip['uuid'], ss_url, report_url, session_id=session_id)
        if not scan_success:
            success = False

        if throttle_time:
            sleep(throttle_time)

    if count > 0:
        print("Successfully scanned", count, "AIPs", file=sys.stderr)

    return success


def main():
    success = 0

    try:
        args = parse_arguments()
    except ArgumentError as e:
        return e

    try:
        fetch_environment_variables(args)
    except ArgumentError as e:
        return e

    if args.command == 'scanall':
        status = scanall(args.ss_url, args.report_url, args.throttle)
    elif args.command == 'scan':
        session_id = str(uuid4())
        status = scan(args.ss_url, args.report_url, session_id=session_id)
    else:
        return Exception('Error: "{}" is not a valid command.'.format(args.command))

    if status is True:
        success = 0
    elif status is False:
        success = 1
    else:
        success = status

    return success


if __name__ == '__main__':
    sys.exit(main())
