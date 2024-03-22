# Duty Day Reporter Script

## Overview

This Python script is designed for comprehensive management and reporting across multiple instances, streamlining analytics gathering, backup management, cloning result log, and system health monitoring via SSH connections. It leverages a JSON file for easy customization according to varied operational needs.
Each server to be accessed need to have a copy of `logger.sh`, the key path can be set in the config file.

Based on the `config.json` entries the script retrieves the information and prints it to the standard output (print) or like json or html.

## Key Features

- **Configuration Validation**: Ensures server configurations are reliable before commencing operations.
- **Automated Actions**: Executes predefined tasks like backups and analytics retrieval on specified servers.
- **Script Updates**: Facilitates both local and remote updates to maintain operational efficiency.
- **Versatile Reporting**: Generates detailed reports in print, JSON, or HTML formats for in-depth analysis.

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

```
pip install paramiko
```

## Configuration

A JSON configuration file is essential for specifying server details, actions to perform, and global script settings. This includes SSH credentials file path, paths for specific operations, and overall script preferences.

## Usage

Run the script with the `--file` parameter to specify the configuration file path. Additional flags are available for configuration checks, script updates, and report generation in various formats.

Example usage:

```
python reporter.py --file config.json
```

To have better readability of the log its recommended to store it into a file and use html mode, json and print is also supported:

```
python reporter.py --file config.json --mode html > report.html
```

## Command Line Arguments

- `--file`: Path to the configuration file (required).
- `--check-config`: Check the configuration file for validity (optional).
- `--check-servers`: Check the external server connections.
- `--update`: Update report and logger files in the host and in the external servers.
- `--mode`: Set the report mode (print, json, html); default is print.

## Example Commands

# Check the configuration file for validity:

```
python reporter.py.py --file path/to/config.json --check-config
```

# Check the external server connections:

```
python reporter.py.py --file path/to/config.json --check-servers
```

# Update scripts from github based on the configuration file:

```
python reporter.py.py --file path/to/config.json --update
```

# Run the logger and generate a report in JSON format:

```
python reporter.py.py --file path/to/config.json --mode json
```

## Configuration File Format

The configuration file must be in JSON format and includes three main sections: config, servers, and actions.

## Config section

- `config`: Global settings applied to the script execution, such as repository URL, branch for updates, and logging type.

- `path`: Path of the repository.

- `logger_path`: (in the instances), path of the logger.sh file (used to update repository too).

- `branch`: Repository branch to target for operations.

- `logtype`: Specifies the logging order or style.

## Servers section

List of server details where each server must have:

- `server_name`: Unique identifier used in actions.servers to reference the server. Its used in the output report too.

- `type`: Specify if the server runs tomcat or docker for analytics. (tomcat or docker).

- `docker_name`: only required by docker type.

- `catalina_file`: Only required to read catalina log of tomcat instances.

- `backups`: Backup .log absolute path.

- `analytics`: Analytics log .log absolute path.

- `cloning`: Cloning log .log absolute path.

- `host`: Hostname or IP address.

- `user`: Username for SSH connection.

- `keyfile`: Path to SSH private key.

- `logger_path`: Repository path on host.

- `proxy`: proxy to be used by github_updater.

## Actions

- `actions`: Defines operations to perform on servers.
  Each action requires:

- `type`: Action type (github_update, backups, monit, analytics, cloning, custom).

- `description`: Human-readable description of the action to show in the report.

- `servers`: List of server_name identifiers to which the action applies.

Some actions has other requirements:

The actions of type `analytics` entry has the following fields in the server entry:

- `type`: docker or tomcat

- `docker_name`: required if the instance is a d2-docker

- `analytics`: The path of the analytics file.

The actions of type `backups` entry has the following fields in the server entry:

- `backups`: The backup log path.

The actions of type `cloning` entry has the following fields in the server entry:

- `cloning`: The cloning log path.

The actions of type `catalinaerrors` entry has the following fields in the server entry:

- `catalina_file`: The catalina log path.

The actions of type `custom` entry has the following fields:

- `command`: The command to be executed in the server.
