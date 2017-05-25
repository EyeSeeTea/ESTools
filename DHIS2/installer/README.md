# dhis2-installer

Shell script to update existing DHIS2 instances (database and, optionally on a hard update, the WAR file)

## Setup

```
$ sudo install -m 775 dhis2_installer.sh /usr/local/bin/dhis2-installer
$ cp dhis2-installer.conf.example $HOME/.dhis2_installer.conf
```

Now customize `$HOME/.dhis2_installer.conf` with your particular setup.

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
$ dhis2-installer run-analytics --server-url="https://admin:district@play.dhis2.org/demo"
```

## Crontab

You may want to run the scripts periodically. Use your user crontab:

```
$ crontab -e
```

For example, this will run all 4 profiles on different times to avoid hogging the machine:

```
$ crontab -l
00 03  * * * /usr/local/bin/dhis2-installer update dev
30 03  * * * /usr/local/bin/dhis2-installer update current
00 04  * * * /usr/local/bin/dhis2-installer update previous1
30 04  * * * /usr/local/bin/dhis2-installer update previous2
```