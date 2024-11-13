# Backups

## Backup Tomcat Instance

### Description

Script meant to either be:
- used with cron to perform periodical backups of a tomcat based DHIS2 instance.
- launched manually to create a manual backup.

It will make a backup of the database and compress the files from DHIS2 home, excluding the apps, if not skipped via `--exclude-files`.
If the `--destination` option is used the backup will also be copied to a remote location.

Backup name is composed by: "BACKUP-`INSTANCE`-`PERIOD`-`NAME`"

### Usage

To manually launch the backup script, use the following command:

```bash
bash /path/to/backup_tomcat_instance.sh [OPTION]....
```

Options:

- `-p, --periodicity [day-in-week | week-in-month | month-in-year]`: Used in scheduled backups to add a period identifier to the backup name. If not set the backup is created with a `TIMESTAMP` in place of the period.
- `-f, --format [custom | plain]`: Type of format used in `pg_dump`, custom means `-Fc` and plain means a compressed `-Fp`.
- `-d, --destination [HOSTNAME]`: The hostname of the remote location where the backup will be copied.
- `-n, --name [NAME]`: Custom name for `NAME` slot, if empty and not a periodic backup will default to "MANUAL".
- `--exclude-audit`: Exclude audit table.
- `--exclude-files`: Exclude the DHIS2 files from the backup.

### Example

Backup with custom name and excluding DHIS2 files:
```bash
bash /path/to/backup_tomcat_instance.sh --name TEST --exclude-files
```

Backup with periodicity, excluding audit table and remote copy:
```bash
bash /path/to/backup_tomcat_instance.sh --periodicity day-in-week --format custom --destination hostname.example --exclude-audit
```