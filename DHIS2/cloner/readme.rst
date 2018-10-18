dhis2_clone
===========

Clone a dhis2 installation from another server.

This program will perform several steps on a running DHIS2 server to
transform it into a clone of a remote one.

The steps are:

* Stop the running tomcat.
* Backup the DHIS2 war file and database.
* Copy the webapps from the remote server into the local machine.
* Empty the local database and fill it with a replica of the remote one.
* Start the tomcat again.

Optionally, it can remove the data (while keeping the metadata) when
copying the remote database (with ``--no-data``). Also, some steps can
be switched off (``--no-backups``, ``--no-webapps``,
``--manual-restart``).

If it is so specified in the configuration file, it will perform some
postprocessing actions (see section below).

Also, it can run some sql scripts on the database before starting the
server again (``--post-sql``). This is especially useful to
automatically upgrade from one version to another (say, 2.29 to 2.30
by running `upgrade-230.sql`_).

.. _`upgrade-230.sql`: https://github.com/dhis2/dhis2-releases/blob/master/releases/2.30/upgrade-230.sql

Usage
-----

  usage: dhis2_clone [-h] [--config CONFIG] [--no-data] [--no-webapps]
                     [--no-backups] [--manual-restart]
                     [--post-sql POST_SQL [POST_SQL ...]] [--no-color]

  Clone a dhis2 installation from another server.

  optional arguments:
    -h, --help            show this help message and exit
    --config CONFIG       file with configuration (default: dhis2_clone.json)
    --no-data             copy only metadata, no data (default: False)
    --no-webapps          don't clone the webapps (default: False)
    --no-backups          don't make backups (default: False)
    --manual-restart      don't stop/start tomcat (default: False)
    --post-sql SQL1_SQL2_etc
                          sql files to run post-clone (default: [])
    --no-color            don't use colored output (default: False)



Configuration
-------------

When running::

  dhis2_clone

it will try to read a configuration file ``dhis2_clone.json`` from the
same directory. An example configuration file is provided in this
repository (`dhis2_clone.json`_).

.. _`dhis2_clone.json`: https://github.com/EyeSeeTea/ESTools/blob/feature/dhis2-clone/DHIS2/cloner/dhis2_clone.json

You can specify a different configuration file with ``--config``.

The sections in the configuration file are:

* ``backups_dir``: directory where it will store the backups.
* ``backup_name``: an identifier that it will append to the name of the war file and database backups.
* ``server_dir_local``: base directory of the tomcat running in the local server.
* ``server_dir_remote``: base directory of the tomcat running in the remote server.
* ``hostname_remote``: name or IP of the machine containing the remote DHIS2 instance. The user running the script is assumed to have ssh access to that machine.
* ``db_local``: URI `conninfo`_ string to connect to the local database.
* ``db_remote``: URI conninfo string to connect to the remote database.
* ``war_local``: name of the local war file (when connecting to the
  web server, this corresponds to the last part of the URL - for
  example, if it is ``dhis2-demo.war``, the webserver will respond at
  ``https://.../dhis2-demo``).
* ``war_remote``: name of the remote war file.
* ``api_local``: if some post-processing steps are applied, this
  section needs to define a ``url``, ``username`` and ``password`` to
  connect to the running DHIS2 system after the cloning.
* ``postprocess``: list of blocks, each containing users (especified
  by ``usernames`` and/or ``fromGroups``) that will be activated, and
  optionally given extra roles if specified (directly from
  ``addRoles`` and/or from ``addRolesFromTemplate`` which will give
  all the roles corresponding to the given user too).

.. _`conninfo`: https://www.postgresql.org/docs/9.3/static/libpq-connect.html#LIBPQ-CONNSTRING

Requirements
------------

This program depends on a few Python standard modules and also:

* ``psycopg2``: to connect to the postgres database.
* ``requests``: to make HTTP requests.

They are available already packaged in most distributions (normally
called ``python-psycopg2`` and ``python-requests``).

Also, it relies on two more modules included here:

* ``process.py``: includes all the post-processing logic.
* ``dhis2api.py``: handles communications with a DHIS2 server through its api.
