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

Any step can be individually switched off (``--no-backups``,
``--no-webapps``, ``--no-db``, ``--manual-restart``).

Also, it can run some sql scripts on the database before starting the
server again (``--post-sql``). This is useful in several
scenarios. For example, to empty the tables that contain the data
(while keeping the metadata), as one would want for a training server
(see the `empty_data_tables_228.sql`_ example). Or it can be used to
automatically upgrade from one version to another (say, 2.29 to 2.30
by running `upgrade-230.sql`_).

.. _`empty_data_tables_228.sql`: https://github.com/EyeSeeTea/ESTools/blob/feature/clone-check/DHIS2/cloner/empty_data_tables_228.sql
.. _`upgrade-230.sql`: https://github.com/dhis2/dhis2-releases/blob/master/releases/2.30/upgrade-230.sql

If it is so specified in the configuration file, it will perform some
postprocessing actions once the server is running again (see section
below).

All the commands run to perform the different steps are printed on the
screen (with color to help identify the steps), and the output of
those commands too. If any step fails, the program will signal an
error and stop all the processing at that point.

Usage
-----

  usage: dhis2_clone [-h] [--check-only] [--no-backups] [--no-webapps] [--no-db]
                   [--no-postprocess] [--manual-restart]
                   [--post-sql POST_SQL [POST_SQL ...]] [--post-clone-scripts]
                   [--update-config] [--no-color]
                   config

Clone a dhis2 installation from another server.

positional arguments:
  config                file with configuration

optional arguments:
  -h, --help            show this help message and exit
  --check-only          check config and exit
  --no-backups          don't make backups
  --no-webapps          don't clone the webapps
  --no-db               don't clone the database
  --no-postprocess      don't do postprocessing
  --manual-restart      don't stop/start tomcat
  --post-sql POST_SQL [POST_SQL ...]
                        sql files to run post-clone
  --post-clone-scripts  execute all py and sh scripts in
                        post_clone_scripts_dir
  --update-config       update the config file
  --no-color            don't use colored output


Configuration
-------------

To invoke the program you need to specify a configuration file, as in::

  $ dhis2_clone config_training.json

An example configuration file is provided in this repository
(`configuration_example.json`_).

.. _`configuration_example.json`: https://github.com/EyeSeeTea/ESTools/blob/feature/clone-check/DHIS2/cloner/configuration_example.json

The sections in the configuration file are:

* ``backups_dir``: directory where it will store the backups.
* ``backup_name``: an identifier that it will append to the name of
  the war file and database backups.
* ``server_dir_local``: base directory of the tomcat running in the
  local server.
* ``server_dir_remote``: base directory of the tomcat running in the
  remote server.
* ``hostname_remote``: name or IP of the machine containing the remote
  DHIS2 instance. The user running the script is assumed to have ssh
  access to that machine.
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
* ``postprocess``: list of blocks, each containing users (specified by
  ``selectUsernames`` and/or ``selectFromGroups``) and an ``action``
  to perform on them (``activate`` to activate them, ``deleteOthers``
  to keep them in exclusive, ``addRoles`` to specify a list of extra
  roles to give, or ``addRolesFromTemplate`` to give a reference
  username whose roles we want to add). Instead of a block, you can
  give a url, and the blocks contained in that url will be added to
  the list of blocks.

.. _`conninfo`: https://www.postgresql.org/docs/9.3/static/libpq-connect.html#LIBPQ-CONNSTRING

Automatic cloning
-----------------

You may want to run the cloning script periodically. For that, you can
use the appropriate users's crontab::

  $ crontab -e

For example, this will run the cloning for a training server every
Saturday night at 22:00::

  $ crontab -l
  00 22 * * 6 /usr/local/bin/dhis2_clone --post-sql /usr/share/dhis2_clone/empty_data_tables.sql /usr/share/dhis2_clone/training.json >> /var/log/dhis2_clone.log 2>&1


Requirements
------------

Python
~~~~~~

This program depends on a few Python standard modules and also:

* ``psycopg2``: to connect to the postgres database.
* ``requests``: to make HTTP requests.

They are available already packaged in most distributions (normally
called ``python-psycopg2`` and ``python-requests``).

Also, it relies on two more modules included here:

* ``process.py``: includes all the post-processing logic.
* ``dhis2api.py``: handles communications with a DHIS2 server through its api.

System programs
~~~~~~~~~~~~~~~

Other than the standard system utilities, the program will need to
have a local installation of:

* ``rsync`` (used with ``ssh`` to copy the remote webapps).
* ``ssh`` (used to copy the remote webapps and to launch the remote dump
  of the database to be cloned).
* ``psql`` (used to modify the local database).
* ``pg_dump`` (used to make a backup of the local database, and a dump
  of the remote one -- so this one needs to exist on ``hostname_remote``
  too).

User permissions
~~~~~~~~~~~~~~~~

The program assumes that it runs with permissions to:

* Read and write all the files in ``<server_dir_local>``, and especially,

  * run the files ``<server_dir_local>/bin/startup.sh`` and
  ``<server_dir_local>/bin/shutdown.sh``.

  * write on ``<server_dir_local>/webapps`` and
    ``<server_dir_local>/files``.
* Write on ``<backups_dir>``.
* Run ``ssh`` to connect to ``<hostname_remote>``.
* Run ``psql`` and ``pg_dump`` on the local host, and on
  ``<hostname_remote>`` thru ``ssh``.
* Read all the files in ``<hostname_remote>:<server_dir_remote>`` thru
  ``ssh``.
* Have read and write access to the local database thru the ``db_local``
  conninfo string, and read access to the remote one thru ``db_remote``.

If it runs any kind of postprocessing (by having an ``api_local`` and
``postprocess`` section in the configuration file), it will also need
permissions to:

* Access the running dhis2 instance thru the ``url``, ``username`` and
  ``password`` present in the ``api_local`` section, and have
  permissions to change the users.

In any case, it does not assume permissions to:

* Delete and create databases.
