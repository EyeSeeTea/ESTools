# Duty Day Reporter Script
## Description
This script generates a report for the DHIS 2 instances contained in the `config.json` file.
This report can recollect the analytics, backups and cloning logs, as well as get the monit events and the disk status.
To access the servers the script uses ssh, the key path and user name can be set in the `reporter.py` file.
Each server to be accessed need to have a copy of `logger.sh` in the same path and this path set in `reporter.py`.

Both types of entries has these common fields:
- type: This field indicates the type of the entry, accepted values are `tomcat`, `docker`, `monit` and `diskspace`.
- server: The server internal name, e.g.: dev, prod, etc.
- host: The server hostname.

The instances of type `tomcat` and `docker` entry has the following fields:
- analytics: Path to the analitycs log.
- backups: Path to the database backup log, used in `tomcat` instances.
- cloning: Path to the docker cloning log, used in `docker` instances.

The instances of type `monit` entry has the following fields:
- monit: The command to be executed to get the monit log.

The instances of type `diskspace` entry has the following fields:
- command: The command to get the disk usage info.

Based on the `config.json` entries the script retrieves the information and prints it to the standard output.

## Usage
Once the `config.json` is set up the script can be executed via:
```
python reporter.py
```

To have better readability of the log its recommended to store it into a file:
```
python reporter.py > report.log
```
