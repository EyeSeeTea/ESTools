## Backup script

The backup includes:

- Mysql dump.
- Postgres dump.
- Any file/directory in the local filesystem specified in a text file (one entry per line)

And can be synced to some destination (local or remote) using efficient incremental backups with [rdiff-backup](http://www.nongnu.org/rdiff-backup/).

## Example

Example that sends the backup to `user@server:dest-directory`:

```
$ cat <<EOF > backup-paths.txt
/var/www/wordpress/wp-config.php
/var/www/mediawiki/LocalSettings.php
/home/ubuntu/.config/scipion-portal/scipion.conf
EOF

$ bash create-backup.sh \
  --files-from=backup-paths.txt \
  --mysql \
  --postgres \
  --destination user@server::dest-directory
```

Note that `rsync-diff` URI needs double colon syntax (`::`).

## Configure databases authentication

### mysql

```
$ cat ~/.my.cnf
[client]
user=USER
password=PASSWORD
```

### postgres

```
$ cat .pgpass
localhost:5432:*:postgres:PASSWORD
```