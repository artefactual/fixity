from __future__ import print_function
from argparse import ArgumentParser
import httplib
import os
import sys

from models import AIP, Session
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

    if args.command == 'scanall':
        aips = storage_service.get_all_aips(storage_service_connection)
        for aip in aips:
            try:
                storage_service.scan_aip(aip, storage_service_connection)
            except storage_service.StorageServiceError:
                success = 1
                print('Requested AIP \"{}\" not present on storage service'.format(aip), file=sys.stderr)
                continue
    elif args.command == 'scan':
        # Ensure the storage service knows about this AIP first;
        # get_single_aip() will raise an exception if the storage service
        # does not have an AIP with that UUID.
        try:
            storage_service.get_single_aip(args.aip, storage_service_connection)
            storage_service.scan_aip(args.aip, storage_service_connection)
        except storage_service.StorageServiceError:
            return Exception('Requested AIP \"{}\" not present on storage service'.format(args.aip))

    return success


if __name__ == '__main__':
    sys.exit(main())
