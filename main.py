from __future__ import print_function
from argparse import ArgumentParser
import json
import httplib
import os
import sys

from models import AIP, Report, Session
import storage_service


class ArgumentError(Exception):
    pass


def store_aips_in_database(aips):
    session = Session()
    for aip in aips:
        if session.query(AIP.uuid).filter_by(uuid=aip['uuid']).count() == 0:
            AIP(uuid=aip['uuid'])
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
        namespace.ss_port = os.environ.get('STORAGE_SERVICE_PORT', 8000)
        namespace.drmc_url = os.environ['DRMC_URL']
    except KeyError:
        raise ArgumentError('Error: A required environment variable was not set')


def scan_message(aip_uuid, status):
    succeeded = "succeeded" if status else "failed"
    return "Fixity scan {} for AIP: {}".format(succeeded, aip_uuid)


def post_report(aip, report, connection):
    body = report.report
    headers = {
        "Content-Type": "application/json"
    }
    url = 'api/fixityreports/{}'.format(aip)
    connection.request('POST', url, body, headers)

    response = connection.getresponse()

    session = Session()
    if not response.status == 201:
        report.posted = False
    else:
        report.posted = True

    session.commit()
    return report.posted


def scan(aip, storage_service_connection, report_connection=None):
    # Ensure the storage service knows about this AIP first;
    # get_single_aip() will raise an exception if the storage service
    # does not have an AIP with that UUID, or otherwise errors out
    # while attempting to respond to the request.
    storage_service.get_single_aip(aip, storage_service_connection)
    try:
        status, report = storage_service.scan_aip(aip, storage_service_connection)
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

    if report_connection and report:
        if not post_report(aip, report, report_connection):
            print("Unable to POST report for AIP {} to remote service".format(aip),
                  file=sys.stderr)

    return status


def scanall(storage_service_connection, report_connection=None):
    success = True

    aips = storage_service.get_all_aips(storage_service_connection)
    for aip in aips:
        scan_success = scan(aip['uuid'], storage_service, report_connection)
        if not scan_success:
            success = False

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
    storage_service_connection = httplib.HTTPConnection(args.ss_url, args.ss_port)
    report_connection = httplib.HTTPConnection(args.drmc_url)

    if args.command == 'scanall':
        status = scanall(storage_service_connection, report_connection)
    elif args.command == 'scan':
        status = scan(args.aip, storage_service_connection, report_connection)
    else:
        return Exception('Error: "{}" is not a valid command.'.format(args.command))

    if not status:
        success = 1

    return success


if __name__ == '__main__':
    sys.exit(main())
