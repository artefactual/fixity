fixity(1) -- Check fixity for AIPs
==================================

## SYNOPSIS

`fixity` command [options] [UUID]

## DESCRIPTION

fixity is a tool to check fixity of Archival Information Packages (AIPs) stored using the Archivematica Storage Service.

fixity can be configured to POST its reports to a remote service after completing every scan. It also retains an internal database which keeps track of every AIP it's scanned and a report of every scan.

fixity requires several environment variables to be exported when it is running; see the section on _ENVIRONMENT VARIABLES_ for information.

## OPTIONS

  * `--throttle` <seconds>:
    Time (in seconds) to wait when scanning multiple AIPs. This can help reduce extended disk load on the filesystem on which the AIPs reside.

## COMMANDS

  * `scan` <UUID>:
    Run a fixity scan on a single AIP, using the specified UUID. If the UUID is malformed, or the Storage Service does not have an AIP with the specified UUID, this will produce an error and exit 1. After the scan completes, a brief report will be printed with information on whether the scan succeeded or failed.

  * `scanall`:
    Run a fixity scan on every AIP registered with the target Storage Service instance. This command does not take any arguments. A brief report will be printed after every AIP is scanned.

    If `--throttle` is passed, then the tool will pause for the specified number of seconds between scans.

## ENVIRONMENT VARIABLES

The following environment variables **must** be exported in the environment for fixity to operate.

  * **STORAGE_SERVICE_URL**:
    The base URL to the storage service instance to scan. Must include the port number for non port 80 installations. Example:
      http://localhost:8000/

  * **REPORT_URL**:
    The base URL to the remote service to which scan reports will be POSTed.
