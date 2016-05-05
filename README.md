fixity
======

Fixity is a simple commandline tool that assists in checking fixity for AIPs stored in Archivematica Storage Service instances.

The Archivematica Storage Service provides a REST API endpoint for checking fixity of AIPs. This tool provides a simple commandline interface to that functionality, in a way that's simple to automate.



Installation
------------

- Checkout or link the code to /usr/lib/archivematica/fixity
- Create a virtualenv in /usr/share/python/fixity, and install fixity and dependencies in it

  ```
  root@host:/# virtualenv /usr/share/python/fixity
  root@host:/# source /usr/share/python/fixity/bin/activate
  (fixity)root@host:/# cd /usr/lib/archivematica/fixity
  (fixity)root@host:/usr/lib/archivematica/fixity# pip install -r requirements.txt
  (fixity)root@host:/usr/lib/archivematica/fixity# python setup.py install
  ```

- Symlink executable to /usr/local/bin

  ```
  root@host:/# ln -s /usr/share/python/fixity/bin/fixity /usr/local/bin/fixity
  ```

- Export required environment variables. Suggested to create a file `/etc/profile.d/fixity.sh`:

  ```
  #!/bin/bash
  export STORAGE_SERVICE_URL=http://localhost:8000
  ...
  ```

- Run the tool with sudo or as root the first time (it is not required to do that afterwards)

Usage
-----

For more information on usage, consult the manpage.



Copyright
---------

Fixity is copyright 2014,2015,2016 Artefactual Systems Inc.
