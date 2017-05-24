# dhis2-installer

Shell script to install DHIS2 instances (database and tomcat WAR)

## Setup

```
install -m 775 dhis2_installer.sh /usr/local/bin/dhis2-installer
cp dhis2_installer.conf.example $HOME/.dhis2_installer.conf
```

## Example

### dhis2-update update

* Update a dhis using a profile:

```
$ dhis2-installer update current
```

* Update a dhis using a profile with custom options:

```
$ dhis2-installer update current --hard
```

### dhis2-update run-analytics

```
$ dhis2-installer run-analytics --server-url="https://admin:district@play.dhis2.org/demo/"
```