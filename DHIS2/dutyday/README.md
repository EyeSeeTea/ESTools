# Duty Day Reporter Script
## Description
This script generates a report for the DHIS 2 instances contained in the `config.json` file.
This report can recollect the analytics, backups and cloning logs, as well as get the monit events and the disk status.
To access the servers the script uses ssh, the key path and user name can be set in the `reporter.py` file.
Each server to be accessed need to have a copy of `logger.sh` in the same path and this path set in `reporter.py`.

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

# Script Title

This script automates the process of updating, monitoring, and reporting on multiple remote servers. It supports various actions including cloning repositories, monitoring system health, managing backups, custom analytics, and executing custom scripts on remote servers.

## Features

- Validates configuration files for server details and action plans.
- Executes local and remote updates based on the provided configuration.
- Supports multiple types of actions like cloning, monitoring, backups, analytics, and custom script execution.
- Generates reports in different formats (print, JSON, HTML) based on execution results.

## Requirements

- Python 3.x
- `paramiko` for SSH connections
- A configuration file in JSON format containing server details and actions to be executed.

## Installation

Ensure Python 3.x is installed on your system. Then, install the required Python package:

pip install paramiko

## Usage
The script is invoked from the command line with various arguments to specify the configuration file, check the configuration, update reports, and define the report mode.

## Command Line Arguments
--file: Path to the configuration file (required).
--check: Check the configuration file for validity (optional).
--update: Update report and logger files (optional).
--mode: Set the report mode (print, printandpush, json, html); default is print.

## Example Commands

# Check the configuration file for validity:
python script_name.py --file path/to/config.json --check

# Update scripts based on the configuration file:
python script_name.py --file path/to/config.json --update

# Run the logger and generate a report in JSON format:
python script_name.py --file path/to/config.json --mode json

## Configuration File Format
The configuration file must be in JSON format and includes three main sections: config, servers, and actions.

## Config section
config: Global settings applied to the script execution, such as repository URL, branch for updates, and logging type.
url: Repository URL to clone or update from.
branch: Repository branch to target for operations.
logtype: Specifies the logging order or style.

## Servers section
List of server details where each server must have:
server_name: Unique identifier used in actions.servers to reference the server.
type: Specify if the server runs tomcat or docker for analytics.
host: Hostname or IP address.
user: Username for SSH connection.
keyfile: Path to SSH private key.
logger_path: Repository path on host.
proxy: proxy to be used by github_updater
Additional fields like proxy, tomcat_folder, docker_name, url, backups may be required based on actions.

## Actions
actions: Defines operations to perform on servers. 
Each action requires:

type: Action type (github_update, backups, monit, analytics, cloning, custom).
description: Human-readable description of the action.
servers: List of server_name identifiers to which the action applies.
Some actions has other requirements:

The actions of type `analytics` entry has the following fields in the server entry:
- type: docker or tomcat
- docker_name: required if the instance is a d2-docker
- tomcat_folder: required if the instance is running on a tomcat
- analytics: The path of the analytics file.

The actions of type `backups` entry has the following fields in the server entry:
- backups: The backup log path.

The actions of type `cloning` entry has the following fields in the server entry:
- cloning: The cloning log path.

The actions of type `custom` entry has the following fields:
- command: The command to be executed in the server.