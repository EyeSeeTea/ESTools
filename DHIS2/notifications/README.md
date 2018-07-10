# Dhis2 notifications

## Setup

* Install the triggers that will create events on interpretation/comments create and edit:

```
$ cat database/triggers.sql | psql [-U USER]
```

* Edit the configuration file: `config.json`.

### Instant email notifications

Use the events stored in the data store to send emails to subscribers of objects:

```
$ node src/notifications.js [-c path/to/config.json] send-instant-notifications
```
