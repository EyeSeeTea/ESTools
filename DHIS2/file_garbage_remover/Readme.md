# DHIS2 File Garbage Remover Scripts

This folder contains two Python scripts designed to manage orphaned resources in DHIS2 instances. 
These scripts identify files with no database references and take appropriate actions depending on the environment, production (tomcat) or testing (docker).

Included Scripts

## file_garbage_remover_tomcat.py

### Description:

Designed for production environments. Identifies orphaned file resources (only documents for now), moves the files to a temporary directory, and archives corresponding database entries into a special table(fileresourcesaudit) before deleting them from the original database table.

### Usage:

Run the script in either test or force mode.

Test Mode (dry-run):

```
export DB_PASSWORD_FILE_G='your_password'
./file_garbage_remover_tomcat.py --test --config /path/to/config.json
```

Force Mode (apply changes):

```
export DB_PASSWORD_FILE_G='your_password'
./file_garbage_remover_tomcat.py --force --config /path/to/config.json
```

config.json File Requirements:
```
{
  "db_host": "",
  "db_port": "",
  "db_name": "",
  "db_user": "",
  "file_base_path": "",
  "temp_file_path": ""
}
```

Ensure file_base_path and temp_file_path exist and are valid directories.

Password should be provided through the environment variable DB_PASSWORD_FILE_G.

Bash wrapper example:
```
#!/bin/bash
MODE="${1:-test}"
[[ "$MODE" != "test" && "$MODE" != "force" ]] && echo "Invalid mode." && exit 1

DB_PASSWORD_FILE_G=db_password

python3 /path/to/script/bin/file_garbage_remover/file_garbage_remover_tomcat.py --config /path/to/script/bin/file_garbage_remover/config.json --$MODE 2>&1 | tee -a /path/to/logs/orphan_cleanup.log

unset DB_PASSWORD_FILE_G
```

## file_garbage_remover_docker.py

### Description:

Intended for d2-docker testing environments. 
Identifies orphaned files in a Dockerized DHIS2 instance and directly deletes them from the container. This script does not archive or move files, permanently removing identified resources.

### Usage:

Run the script specifying the Docker DHIS2 instance:

```
./file_garbage_remover_docker.py --instance docker.eyeseetea.com/project/dhis2-data:2.41-test
```

### Operation:

Executes an SQL query within the DHIS2 container using d2-docker run-sql.

Copies the generated file list into the container.

Deletes identified files directly inside the container.

# Precautions

Production Environments: Always use --test mode before using --force to verify intended changes.

Docker/Test Environments: Files deleted by file_garbage_remover_docker.py cannot be recovered.