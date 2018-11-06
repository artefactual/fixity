fixity
======

Fixity is a simple commandline tool that assists in checking fixity for AIPs
stored in Archivematica Storage Service instances.

The Archivematica Storage Service provides a REST API endpoint for checking
fixity of AIPs. This tool provides a simple commandline interface to that
functionality, in a way that's simple to automate.

Installation
------------

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

3. Create a symlink from the executable to /usr/local/bin.  You must still be
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

Usage
-----

For more information on usage, consult the [manpage](docs/fixity.1.md).

Copyright
---------

Fixity is copyright 2014,2015,2016 Artefactual Systems Inc.
