from __future__ import print_function
from argparse import ArgumentParser
from datetime import datetime
import json
import os
import sys
from uuid import uuid4
from time import sleep
import traceback

from .models import Report, Session
from . import reporting
from . import storage_service


class ArgumentError(Exception):
    pass


def validate_arguments(args):
    if args.command == 'scan' and not args.aip:
        raise ArgumentError('An AIP UUID must be specified when scanning a single AIP')


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('command', choices=['scan', 'scanall'],
        help='Command to run.')
    parser.add_argument('aip', nargs='?', help="If 'scan', UUID of the AIP to scan")
    parser.add_argument('-d', '--debug', action='store_true',
        help='Print extra debugging output.')
    parser.add_argument('--throttle', type=int, default=0,
        help='Time in seconds to wait between scanning multiple AIPs.')
    parser.add_argument('--force-local', action='store_true',
        help="Force a local fixity check on the Storage Service.")
    args = parser.parse_args()

    validate_arguments(args)
    return args


def _get_environment_variable(var):
    try:
        return os.environ[var]
    except KeyError as e:
        raise ArgumentError("Missing environment variable: {}".format(e.args[0]))


def fetch_environment_variables(namespace):
    namespace.ss_url = _get_environment_variable('STORAGE_SERVICE_URL')
    if not namespace.ss_url.endswith('/'):
        namespace.ss_url = namespace.ss_url + '/'
    namespace.ss_user = _get_environment_variable('STORAGE_SERVICE_USER')
    namespace.ss_key = _get_environment_variable('STORAGE_SERVICE_KEY')

    if 'REPORT_URL' in os.environ:
        namespace.report_url = _get_environment_variable('REPORT_URL')
        if not namespace.report_url.endswith('/'):
            namespace.report_url = namespace.report_url + '/'

    # These two parameters are optional; not all reporting services
    # require any authentication.
    try:
        namespace.report_user = os.environ['REPORT_USERNAME']
        namespace.report_pass = os.environ['REPORT_PASSWORD']
    except KeyError:
        namespace.report_user = namespace.report_pass = None


def scan_message(aip_uuid, status, message):
    if status is True:
        succeeded = 'succeeded'
    elif status is False:
        succeeded = 'failed'
    elif status is None:
        succeeded = "didn't run"
    else:
        succeeded = 'returned an unknown status'
    output = "Fixity scan {} for AIP: {}".format(succeeded, aip_uuid)
    if message:
        output += ' ({})'.format(message)
    return output


def scan(aip, ss_url, ss_user, ss_key, session, report_url=None, report_auth=(), session_id=None, force_local=False):
    """
    Instruct the storage service to scan a single AIP.

    This first attempts to query the storage service about the AIP,
    to ensure the storage service still has a record of it, then
    runs a fixity scan.

    :param str aip: AIP UUID string.
    :param str ss_url: The base URL to a storage service installation.
    :param str ss_user: Storage service user to authenticate as
    :param str ss_key: API key of the storage service user
    :param str report_url: The base URL to a server to which the report will be POSTed after the scan completes. If absent, the report will not be     transmitted.
    :param report_auth: Authentication for the report_url. Tupel of (user, password) for HTTP auth.
    :param session_id: Identifier for this session, allowing every scan from one run to be identified.
    :param bool force_local: If True, will will request the Storage Service to perform a local fixity check, instead of using the Space's fixity (if available).
    """

    # Ensure the storage service knows about this AIP first;
    # get_single_aip() will raise an exception if the storage service
    # does not have an AIP with that UUID, or otherwise errors out
    # while attempting to respond to the request.
    storage_service.get_single_aip(aip, ss_url, ss_user, ss_key)

    start_time = datetime.utcnow()

    try:
        if report_url:
            reporting.post_pre_scan_report(
                aip, start_time,
                report_url=report_url, report_auth=report_auth,
                session_id=session_id
            )
    except reporting.ReportServiceException:
        print(
            "Unable to POST pre-scan report to {}".format(report_url),
            file=sys.stderr
        )

    try:
        status, report = storage_service.scan_aip(
            aip, ss_url, ss_user, ss_key, session,
            start_time=start_time,
            force_local=force_local,
        )
        report_data = json.loads(report.report)
        print(scan_message(aip, status, report_data['message']), file=sys.stderr)
    except Exception as e:
        print(e.message, file=sys.stderr)
        status = None
        if hasattr(e, 'report') and e.report:
            report = e.report
        # Certain classes of exceptions will not return reports because no
        # scan was even attempted; report the exception in that case.
        else:
            report_dict = {
                "success": "None",
                "message": "Exception encountered while scanning AIP {}: {} ({})".format(aip, type(e).__name__, e.message),
                "traceback": traceback.format_exc(),
                "errors": None
            }

            report = Report(
                aip_id=aip, report=json.dumps(report_dict), success=None,
                begun=start_time, ended=start_time, posted=False
            )

    if report_url:
        try:
            reporting.post_success_report(aip, report, report_url, report_auth=report_auth, session_id=session_id)
        except reporting.ReportServiceException:
            print("Unable to POST report for AIP {} to remote service".format(aip),
                  file=sys.stderr)

    return status


def scanall(ss_url, ss_user, ss_key, session, report_url=None, report_auth=(), throttle_time=0, force_local=False):
    """
    Run a fixity scan on every AIP in a storage service instance.

    :param str ss_url: The base URL to a storage service installation.
    :param str ss_user: Storage service user to authenticate as
    :param str ss_key: API key of the storage service user
    :param str report_url: The base URL to a server to which the report will be POSTed after the scan completes. If absent, the report will not be transmitted.
    :param report_auth: Authentication for the report_url. Tupel of (user, password) for HTTP auth.
    :param int throttle_time: Time to wait between scans.
    :param bool force_local: If True, will will request the Storage Service to perform a local fixity check, instead of using the Space's fixity (if available).
    """
    success = True

    # The same session ID will be used for every scan,
    # allowing every scan from one run to be identified.
    session_id = str(uuid4())

    try:
        aips = storage_service.get_all_aips(ss_url, ss_user, ss_key)
    except storage_service.StorageServiceError as e:
        return e
    count = len(aips)
    for aip in aips:
        try:
            scan_success = scan(
                aip['uuid'], ss_url, ss_user, ss_key, session,
                report_url=report_url, report_auth=report_auth,
                session_id=session_id, force_local=force_local,
            )
            if not scan_success:
                success = False
        except Exception as e:
            print("Internal error encountered while scanning AIP {} ({})".format(aip['uuid'], type(e).__name__))

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

    session = Session()

    status = False

    if args.report_user and args.report_pass:
        auth = (args.report_user, args.report_pass)
    else:
        auth = ()

    try:
        report_url = args.report_url if ('report_url' in args) else None

        if args.command == 'scanall':
            status = scanall(
                args.ss_url, args.ss_user, args.ss_key, session,
                report_url=report_url, report_auth=auth,
                throttle_time=args.throttle, force_local=args.force_local
            )
        elif args.command == 'scan':
            session_id = str(uuid4())
            status = scan(
                args.aip, args.ss_url, args.ss_user, args.ss_key, session,
                report_url=report_url, report_auth=auth,
                session_id=session_id, force_local=args.force_local,
            )
        else:
            return Exception('Error: "{}" is not a valid command.'.format(args.command))

        session.commit()
    except Exception as e:
        session.rollback()
        if args.debug:
            traceback.print_exc()
        return e
    finally:
        session.close()

    if status is True:
        success = 0
    elif status is False:
        success = 1
    else:
        success = status

    return success


if __name__ == '__main__':
    sys.exit(main())
