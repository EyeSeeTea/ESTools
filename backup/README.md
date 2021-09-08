## Description

Backup dhis2 database to S3.

### Setup

```
$ apt install awscli
```

Create a profile `dhis2` in the file `~/.aws/credentials` with your S3 credentials:

```
[dhis2]
aws_access_key_id = ACCESS_KEY
aws_secret_access_key = SECRET_KEY
region = us-east-1
```

### Usage

```
$ bash backup-dhis2-db.sh DATABASE_NAME DESTINATION s3://BUCKET daily|weekly|monthly
```

For example:

```
$ bash backup-dhis2-db.sh dhis2 /var/local/backups s3://occ-app-dhis daily
```

### S3 commands

```
$ aws --profile dhis2 --endpoint-url https://s3.theark.cloud s3 ls s3://occ-app-dhis --recursive
```
