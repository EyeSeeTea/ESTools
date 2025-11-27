# DHIS2 File Garbage Remover Scripts

This folder contains two Python scripts designed to manage orphaned resources in DHIS2 instances. 
These scripts identify files with no database references and take appropriate actions depending on the environment, production (tomcat) or testing (docker).

Included Scripts

## main.py (recommended entry point)

Run cleanup (tomcat or docker) and optionally send a notification in one command. Dry-run is the default unless you add `--force`.

### Example (docker cleanup + notify using webhook from config.json)
```
python3 main.py \
  --mode docker \
  --docker-instance docker.eyeseetea.com/widpit/dhis2-data:2.41-widp-dev-test \
  --csv-path /tmp/fg_docker.csv \
  --config /path/to/config.json \
  --notify-title "Orphans widp-dev-test"
```
- Add `--force` to delete/move for real (tomcat) or delete in container (docker).  
- Add `--notify-test` to print the payload instead of sending.  
- To notify only (no cleanup): `python3 main.py --notify-only --csv-path /tmp/fg.csv --config /path/to/config.json --notify-title "..." [--notify-test]`
- To skip sending and save in CSV as notified: `--save-all-as-notified`.

### Example (tomcat cleanup, dry-run, save as nnotified)
```
DB_PASSWORD_FG=your_password python3 main.py \
  --config /path/to/config.json \
  --csv-path /tmp/fg_tomcat.csv \
  --save-all-as-notified
```
Add `--force` to move/delete files and files in DB.

config.json needs the cleanup settings plus the webhook (if you want notifications):
```
{
  "db_host": "",
  "db_port": "",
  "db_name": "",
  "db_user": "",
  "file_base_path": "",
  "temp_file_path": "",
  "webhook-url": "https://your.webhook.url",
  "notify-http-proxy": "http://openproxy.who.int:8080",
  "notify-https-proxy": "http://openproxy.who.int:8080"
}
```

## file_garbage_remover_tomcat.py

### Description:

Designed for production environments. Identifies orphaned file resources (documents or datavalues (files or images attached to a value)), moves the files to a temporary directory, and archives corresponding database entries into a special table(fileresourcesaudit) before deleting them from the original database table.

### Usage:

Run the script in either test or force mode.

Test Mode (dry-run):

```
export DB_PASSWORD_FG='your_password'
./file_garbage_remover_tomcat.py --test --config /path/to/config.json
```

Force Mode (apply changes):

```
export DB_PASSWORD_FG='your_password'
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

Password should be provided through the environment variable DB_PASSWORD_FG.

Bash wrapper example:
```
#!/bin/bash
MODE="${1:-test}"
[[ "$MODE" != "test" && "$MODE" != "force" ]] && echo "Invalid mode." && exit 1

DB_PASSWORD_FG=db_password

python3 /path/to/script/bin/file_garbage_remover/file_garbage_remover_tomcat.py --config /path/to/script/bin/file_garbage_remover/config.json --$MODE 2>&1 | tee -a /path/to/logs/orphan_cleanup.log

unset DB_PASSWORD_FG
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
