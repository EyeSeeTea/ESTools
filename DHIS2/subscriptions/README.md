# Dhis2 notifications

## Setup

* Install the PostgreSQL triggers that will store an event every time an interpretation or comments is created or edited:

```
$ cat database/triggers.sql | psql [-U USER]
```

* Edit the configuration file: `config.json`.

* Add crontab entries (`crontab -e`) to send notifications and newsletter to subscribers (see _Commands_ section). An example:

```
00 8 * * MON chronic /path/to/

```



## Commands

### Send instant email notifications

Send emails to subscribers of objects (charts, eventCharts, maps, reportTables, eventReports):

```
$ node src/notifications.js [-c path/to/config.json] send-notifications
```

### Send newsletter

Send a weely report of interpretations to subscribers of their parent objects:

```
$ node src/notifications.js [-c path/to/config.json] send-newsletter
```