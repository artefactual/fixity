from __future__ import print_function
from argparse import ArgumentParser
import json
import os
import sys

from models import AIP, Report, Session
import storage_service

import requests


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
        namespace.drmc_url = os.environ['DRMC_URL']
    except KeyError:
        raise ArgumentError('Error: A required environment variable was not set')


def scan_message(aip_uuid, status):
    succeeded = "succeeded" if status else "failed"
    return "Fixity scan {} for AIP: {}".format(succeeded, aip_uuid)


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


def scan(aip, ss_url, report_url=None):
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
    try:
        status, report = storage_service.scan_aip(aip, ss_url)
        print(scan_message(aip, status), file=sys.stderr)
    except (storage_service.StorageServiceError, storage_service.InvalidUUID) as e:
        print(e.message, file=sys.stderr)
        status = None
        if hasattr(e, 'report') and e.report:
            report = e.report
        # Certain classes of exceptions will not return reports because no
        # scan was even attempted; nothing to POST in that case.
        else:
            report = None

    if report_url and report:
        if not post_report(aip, report, report_url):
            print("Unable to POST report for AIP {} to remote service".format(aip),
                  file=sys.stderr)

    return status


def scanall(ss_url, report_url=None):
    """
    Run a fixity scan on every AIP in a storage service instance.

    ss_url should be the base URL to a storage service installation.
    report_url can be the base URL to a server to which the report will
    be POSTed after the scan completes. If absent, the report will not be
    transmitted.
    """
    success = True

    aips = storage_service.get_all_aips(ss_url)
    count = len(aips)
    for aip in aips:
        scan_success = scan(aip['uuid'], ss_url, report_url)
        if not scan_success:
            success = False

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
        status = scanall(args.ss_url, args.drmc_url)
    elif args.command == 'scan':
        status = scan(args.ss_url, args.drmc_url)
    else:
        return Exception('Error: "{}" is not a valid command.'.format(args.command))

    if not status:
        success = 1

    return success


if __name__ == '__main__':
    sys.exit(main())
