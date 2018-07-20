# Dhis2 notifications

## Setup

* Install the PostgreSQL triggers that will store an event every time an interpretation or comments is created or edited:

```
$ cat database/triggers.sql | psql [-U USER]
```

* Edit the configuration file: `config.json`.

* Install the package globally from sources:

```
$ npm install -g ESTools/DHIS2/subscriptions
# Check that the executable has been installed and see its path (depends on node configuration)
$ which dhis2-subscriptions
/home/user/.npm-global/bin/dhis2-subscriptions
```

* Add crontab entries (`crontab -e`) to send notifications and newsletter to subscribers (see _Commands_ section). An example:

```
00 8 * * MON chronic /path/to/dhis2-subscriptions --config-file=/path/to/your/config.json send-newsletters
*/15 * * * * chronic /path/to/dhis2-subscriptions --config-file=/path/to/your/config.json send-notifications
```

## Commands

### Send instant email notifications

Send emails to subscribers of objects (charts, eventCharts, maps, reportTables, eventReports):

```
$ node src/notifications.js [-c path/to/config.json] send-notifications
```

### Send newsletter

Send a weekly report of interpretations to subscribers of their parent objects:

```
$ node src/notifications.js [-c path/to/config.json] send-newsletters
```