# dhis2-installer

Shell script to update existing DHIS2 instances (database and, optionally on a hard update, the WAR file)

## Setup

```
$ sudo install -m 775 dhis2_installer.sh /usr/local/bin/dhis2-installer
$ cp dhis2-installer.conf.example $HOME/.dhis2_installer.conf
```

Now customize `$HOME/.dhis2_installer.conf` with your particular setup.

## Usage

```
dhis2-installer [-h | --help] <command> [<command_options>]

Commands:

  update [PROFILE] [OPTIONS]  Update an existing DHIS2 Tomcat instance
  run-analytics URL|PROFILE [URL|PROFILE...]  Run analytics
  check-servers URL|PROFILE [URL|PROFILE...]  Check server status

<update> options:

  --soft  Drop current DB and install a fresh one (keeping existing DHIS2 war) [default]
  --hard  Drop current DB, install a fresh one and update DHIS war

  --data-directory=DIRECTORY  Directory to store downloaded files and repos
  --logs-directory=DIRECTORY  Directory to store logs

  --db-name=NAME   Database name
  --db-source=URL  File URL or github blob URL (repo will be cloned)

  --start-command=NAME  Command to start the DHIS2 server
  --stop-command=NAME   Command to stop the DHIS2 server

  --war-source=URL             URL of the DHIS2 WAR to install (only on --hard)
  --war-destination=DIRECTORY  Directory to save DHIS2 war (only on --hard)

  --run-analytics       Run analytics after the update (requires --server-url)
  --post-scripts=PATH   Run post scripts in directory after the update (requires --server-url)
```

## Examples

### Command <update>


* Update a DHIS2 instance using the profile _current_:

```
$ dhis2-installer update current
```

* Update a DHIS2 instance using the profile _previous1_ with extra/overriding options:

```
$ dhis2-installer update previous1 --hard
```

### Command <run-analytics>

```
$ dhis2-installer run-analytics https://admin:district@play.dhis2.org/demo dev previous1
```

### Command <check-servers>

```
$ dhis2-installer check-servers https://admin:district@play.dhis2.org/demo dev previous1
```

## Crontab

You may want to run the scripts periodically. Use your user crontab:

```
$ crontab -e
```

For example, this will run four profiles on different times to avoid hogging the machine:

```
$ crontab -l
00 03  * * * /usr/local/bin/dhis2-installer update dev --hard
30 03  * * * /usr/local/bin/dhis2-installer update current
00 04  * * * /usr/local/bin/dhis2-installer update previous1
30 04  * * * /usr/local/bin/dhis2-installer update previous2
```
