# Create a backup in servers

The backup includes:

- Mysql dump.
- Postgres dump.
- Any file/directory in the local filesystem specified in a text file (one entry per line)

And can be synced to some destination (local or remote) using efficient incremental backups with [rdiff-backup](http://www.nongnu.org/rdiff-backup/).

Example that sends the backup to `user@server:dest-directory`:

```
$ cat <<EOF > backup-paths.txt
/var/www/wordpress/wp-config.php
/var/www/mediawiki/LocalSettings.php
/home/ubuntu/.config/scipion-portal/scipion.conf
EOF

$ bash create-backup.sh \
  --files-from=backup-paths.txt \
  --mysql-password=PASSWORD1 \
  --postgres-password=PASSWORD2 \
  --destination user@server::dest-directory
```

Note that `rsync-diff` URI needs double colon syntax (`::`).