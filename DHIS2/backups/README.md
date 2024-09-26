# Backups

## Backup Tomcat Instance

### Description

Script meant to either be:
- used with cron to perform periodical backups of a tomcat based DHIS2 instance.
- launched manually to create a manual backup.

It will make a backup of the database and compress the files from DHIS2 home (excluding the apps).
If the `--destination` option is used the backup will also be copied to a remote location.

### Usage

To manually launch the backup script, use the following command:

```bash
bash /path/to/backup_tomcat_instance.sh --format custom --exclude-audit
```

Options:

- `-p, --periodicity [day-in-week | week-in-month | month-in-year]`: Used in scheduled backups to add a period identifier to the backup name. If not set the backup is created with a MANUAL-TIMESTAMP suffix.
- `-f, --format [custom | plain]`: Type of format used in `pg_dump`, custom means -Fc and plain means a compressed -Fp.
- `-d, --destination [hostname]`: The hostname of the remote location where the backup will be copied.
- `--exclude-audit`: Exclude audit table.