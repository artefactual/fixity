# fixity

[![PyPI version](https://img.shields.io/pypi/v/fixity.svg)](https://pypi.python.org/pypi/fixity)
[![GitHub CI](https://github.com/artefactual/fixity/actions/workflows/test.yml/badge.svg)](https://github.com/artefactual/fixity/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/artefactual/fixity/branch/master/graph/badge.svg?token=wiga5iF7CK)](https://codecov.io/gh/artefactual/fixity)

## Table of contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [About](#about)
- [Check fixity](#check-fixity)
- [Fixity errors](#fixity-errors)
  - [Information has been deleted from a file](#information-has-been-deleted-from-a-file)
  - [A character in a file has been modified](#a-character-in-a-file-has-been-modified)
  - [A file has been removed from the package](#a-file-has-been-removed-from-the-package)
  - [A file has been added to the package](#a-file-has-been-added-to-the-package)
  - [A manifest has been removed from the package](#a-manifest-has-been-removed-from-the-package)
  - [How this looks in the Storage Service](#how-this-looks-in-the-storage-service)
- [Installation](#installation)
- [Usage](#usage)
- [Security](#security)
- [Copyright](#copyright)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## About

Fixity is a command line tool that assists in checking fixity for AIPs stored
in the Archivematica Storage Service.

*"Fixity"* in digital preservation terms is defined as *"the assurance that a
digital file has remained unchanged, i.e. fixed."*
[(Bailey, 2014)](https://blogs.loc.gov/thesignal/2014/04/protect-your-data-file-fixity-and-data-integrity/)
and more information about that, and the concept of checksums, can be found in
the Digital Preservation Coalition's (DPC)
[Digital Preservation Handbook](https://www.dpconline.org/handbook/technical-solutions-and-tools/fixity-and-checksums).

Fixity is a client application that calls the Storage Service's
[Check Fixity](https://wiki.archivematica.org/Storage_Service_API#Check_fixity)
API endpoint for a single AIP or for each AIP in the Storage Service.

## Check fixity

The Storage Service's Check Fixity endpoint can be used to trigger a fixity
check on an individual package. When the Fixity client calls this endpoint, the
checking is done in the Storage Service itself.

Fixity aggregates results and makes it easy to do this across all packages.

To trigger fixity checking for a package, we need to know the AIP UUID and the
Storage Service authorization parameters.

The URL is constructed as follows:
`http://127.0.0.1:62081/api/v2/file/<AIP UUID>/check_fixity/`

And we can supply authentication information in a HTTP request using a command
line tool such as [HTTPie](https://httpie.org):

```shell
http -v --pretty=format \
    GET "http://127.0.0.1:62081/api/v2/file/5e21dd0d-190e-4ffb-b752-76d860bea898/check_fixity/" \
    Authorization:"ApiKey test:test"
```

This results in the following JSON output showing us that the Fixity check was
a 'success', that is, there were no errors:

```json
{
    "failures": {
        "files": {
            "changed": [],
            "missing": [],
            "untracked": []
        }
    },
    "message": "",
    "success": true,
    "timestamp": null
}
```

This detailed JSON output is recorded in Fixity's internal database. Summary
information about errors is printed to the console. The output for package
`5e21dd0d-190e-4ffb-b752-76d860bea898` would simply look as follows:

```console
Fixity scan succeeded for AIP: 5e21dd0d-190e-4ffb-b752-76d860bea898
```

The Check Fixity endpoint updates the Storage Service `fixitylog` model with
details of the last check completed.

Storage Service users can see the last `Fixity Date` and `Fixity Status` in the
Storage Service Packages panel by going to `{storage-service-url}/packages/`

Administrators of the Storage Service can query the Storage Service database as
follows:

```sql
select
   package_id as "AIP UUID",
   datetime_reported as "Fixity Last Checked",
   success,
   error_details
from locations_fixitylog
where package_id = '5e21dd0d-190e-4ffb-b752-76d860bea898'
order by datetime_reported desc
limit 1;
```

And we can see the details of the check in the SQL output:

```sql
+--------------------------------------+----------------------------+---------+---------------+
| AIP UUID                             | Fixity Last Checked        | success | error_details |
+--------------------------------------+----------------------------+---------+---------------+
| 5e21dd0d-190e-4ffb-b752-76d860bea898 | 2018-11-06 11:20:43.634188 |       1 | NULL          |
+--------------------------------------+----------------------------+---------+---------------+
```

## Fixity errors

The Storage Service can detect multiple categories of error. Some are shown as
outputs of Fixity below with the corresponding detailed information that can
be accessed from Fixity's database:

### Information has been deleted from a file

```console
Fixity scan failed for AIP: 5e21dd0d-190e-4ffb-b752-76d860bea898 (Oxum error.
Found 10 files and 126404 bytes on disk; expected 10 files and 126405 bytes.)
```

**Detail:**

```json
{
    "failures": {
        "files": {
            "changed": [],
            "missing": [],
            "untracked": []
        }
    },
    "finished": 1541505247,
    "message": "Oxum error.  Found 10 files and 126404 bytes on disk; expected 10 files and 126405 bytes.",
    "started": 1541505247,
    "success": false,
    "timestamp": null
}
```

### A character in a file has been modified

```console
Fixity scan failed for AIP: 5e21dd0d-190e-4ffb-b752-76d860bea898 (invalid bag)
```

**Detail:**

```json
{
    "failures": {
        "files": {
            "changed": [
                {
                    "actual": "6ea7859a4edb8406aae0dfdf5abda9db97eeb8b416922b7356082ab55c9e4161",
                    "expected": "9fd57a8c09e0443de485cf51b68ad8ef54486454434daed499d2f686b7efc2b4",
                    "hash_type": "sha256",
                    "message": "data/objects/one_file/one_file.txt checksum validation failed (alg=sha256 expected=9fd57a8c09e0443de485cf51b68ad8ef54486454434daed499d2f686b7efc2b4 found=6ea7859a4edb8406aae0dfdf5abda9db97eeb8b416922b7356082ab55c9e4161)",
                    "path": "data/objects/one_file/one_file.txt"
                }
            ],
            "missing": [],
            "untracked": []
        }
    },
    "finished": 1541505387,
    "message": "invalid bag",
    "started": 1541505386,
    "success": false,
    "timestamp": null
}
```

### A file has been removed from the package

```console
Fixity scan failed for AIP: 5e21dd0d-190e-4ffb-b752-76d860bea898 (Oxum error.
Found 9 files and 126386 bytes on disk; expected 10 files and 126405 bytes.)
```

**Detail:**

```json
{
    "failures": {
        "files": {
            "changed": [],
            "missing": [],
            "untracked": []
        }
    },
    "finished": 1541505645,
    "message": "Oxum error.  Found 9 files and 126386 bytes on disk; expected 10 files and 126405 bytes.",
    "started": 1541505645,
    "success": false,
    "timestamp": null
}
```

### A file has been added to the package

```console
Fixity scan failed for AIP: 5e21dd0d-190e-4ffb-b752-76d860bea898 (Oxum error.
Found 11 files and 126405 bytes on disk; expected 10 files and 126405 bytes.)
```

**Detail:**

```json
{
    "failures": {
        "files": {
            "changed": [],
            "missing": [],
            "untracked": []
        }
    },
    "finished": 1541505549,
    "message": "Oxum error.  Found 11 files and 126405 bytes on disk; expected 10 files and 126405 bytes.",
    "started": 1541505549,
    "success": false,
    "timestamp": null
}

```

### A manifest has been removed from the package

```console
Fixity scan failed for AIP: 5e21dd0d-190e-4ffb-b752-76d860bea898 (Missing
manifest file)
```

**Detail:**

```json
{
    "failures": {
        "files": {
            "changed": [],
            "missing": [],
            "untracked": []
        }
    },
    "finished": 1541505815,
    "message": "Missing manifest file",
    "started": 1541505815,
    "success": false,
    "timestamp": null
}
```

### How this looks in the Storage Service

For any error in the Fixity check the Storage Service database maintains a
summary log, see for example when data in a file has been modified:

```sql
+--------------------------------------+----------------------------+---------+---------------+
| AIP UUID                             | Fixity Last Checked        | success | error_details |
+--------------------------------------+----------------------------+---------+---------------+
| 5e21dd0d-190e-4ffb-b752-76d860bea898 | 2018-11-06 12:10:22.981609 |       0 | invalid bag   |
+--------------------------------------+----------------------------+---------+---------------+
```

## Installation

Installation of Fixity can be completed with the following steps:

1. Checkout or link the code to `/usr/lib/archivematica/fixity`
   1. Go to `/usr/lib/archivematica/`

      ```bash
      user@root:~$ cd /usr/lib/archivematica/
      ```

   2. Clone the code:

      ```bash
      user@root:/usr/lib/archivematica/$ git clone https://github.com/artefactual/fixity.git
      ```

      Once this is complete, the directory `/usr/lib/archivematica/fixity`
      should exist. `cd` back to the home directory

      ```bash
      user@root:/usr/lib/archivematica/$ cd
      ```

2. Create a virtualenv in `/usr/share/python/fixity`, and install fixity and
   dependencies in it

   1. Switch to root

      ```bash
      user@root:~$ sudo -i
      ```

   2. Run:

      ```bash
      root@host:~# virtualenv /usr/share/python/fixity
      root@host:~# source /usr/share/python/fixity/bin/activate
      (fixity)root@host:~# cd /usr/lib/archivematica/fixity
      (fixity)root@host:/usr/lib/archivematica/fixity# pip install -r requirements.txt
      (fixity)root@host:/usr/lib/archivematica/fixity# python setup.py install
      ```

3. Create a symlink from the executable to `/usr/local/bin`.  You must still be
   root.

   ```bash
   (fixity)root@host:/usr/lib/archivematica/fixity# ln -s /usr/share/python/fixity/bin/fixity /usr/local/bin/fixity
   ```

4. Export required environment variables. For ease of use later, creating
   `/etc/profile.d/fixity.sh` is recommended:

   1. To create the file:

      ```bash
      (fixity)root@host:/usr/lib/archivematica/fixity# touch /etc/profile.d/fixity.sh
      (fixity)root@host:/usr/lib/archivematica/fixity# nano /etc/profile.d/fixity.sh
      ```

   2. You are now editing the environment variables file. You should use the
      URL of your Storage Service, and the username and API key of one Storage
      Service user. Replace the URL, user and key with your data.

      ```bash
      #!/bin/bash
      export STORAGE_SERVICE_URL=http://localhost:8000
      export STORAGE_SERVICE_USER=myuser
      export STORAGE_SERVICE_KEY=myapikey
      ```

   3. Optionally, if you are using Fixity with a reporting service, you can
      also add:

      ```bash
      export REPORT_URL=http://myurl.com
      export REPORT_USERNAME=myuser
      export REPORT_PASSWORD=mypassword
      ```

   4. Load the variables from the file.

      ```bash
      (fixity)root@host:/usr/lib/archivematica/fixity# source /etc/profile.d/fixity.sh
      ```

5. Run the tool with sudo or as root the first time.  Subsequent runs can be
   with any user.

   ```bash
   (fixity)root@host:/usr/lib/archivematica/fixity# fixity scanall
   ```

6. To exit the virtualenv:

   ```bash
   (fixity)root@host:/usr/lib/archivematica/fixity# deactivate
   root@host:/usr/lib/archivematica/fixity#
   ```

   And to exit the root user:

   ```bash
   root@host:/usr/lib/archivematica/fixity# exit
   user@host:~$
   ```

7. After the initial install, to run fixity you only need to load the variables
   you defined earlier and run fixity.

   ```bash
   user@host:~$ source /etc/profile.d/fixity.sh
   user@host:~$ fixity scanall
   ```

## Usage

For more information on usage, consult the [manpage](docs/fixity.1.md).

## Security

If you have a security concern about Archivematica or any of its companion
repositories, please see the
[Archivematica security policy](https://github.com/artefactual/archivematica/security/policy)
for information on how to safely report a vulnerability.

## Copyright

Fixity is copyright 2014-2018 Artefactual Systems Inc.
