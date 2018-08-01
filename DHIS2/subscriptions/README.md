# Dhis2 notifications

## Setup

* Install the PostgreSQL triggers that create an event whenever an interpretation/comment is created/edited:

```
$ cat database/triggers.sql | psql [DATABASE_NAME] [-U USER]
```

* Build the assets:

```
$ yarn install
$ yarn build
```

This will create directory `build/` containing the directory structure of the assets that needs to be uploaded to a public server.

* Edit the configuration file: `config.json` (details below)

* Install the package from sources:

```
$ [sudo] npm install -g .

# Check that the executable has been installed and where (it will depend on your specific node configuration)
$ which dhis2-subscriptions
/home/someuser/.npm-global/bin/dhis2-subscriptions
```

* Add crontab entries (`crontab -e`) to send notifications and newsletters to subscribers. An example:

```
*/5 * * * *   chronic /path/to/bin/dhis2-subscriptions --config-file=/path/to/your/config.json send-notifications
00  8 * * MON chronic /path/to/bin/dhis2-subscriptions --config-file=/path/to/your/config.json send-newsletters
```

## Configuration file (`config.json`)

```
{
    // Global locale code (used for literal translations)
    "locale": "en",

    // Images (icons and dhis2 resources) must be uploaded to a public server (local or remote)
    "assets": {
        "url": "http://some-public-server.com/resources",
        // Copy PNG downloaded from DHIS2 to the folder of the public server (use cp/sc/.rsync/...)
        "upload": "cp {{files}} /path/to/build/resources/"
    },

    // DHIS2 public URL
    "publicUrl": "http://localhost:8080",

    // Cache file to store timestamp of previous sent operations
    "cacheFilePath": ".notifications-cache.json",

    // DHIS2 Api details
    "api": {
        "url": "http://localhost:8080/api/",
        "auth": {
            "username": "admin",
            "password": "district"
        }
    },

    // DHIS2 dataStore details where events are stored
    "dataStore": {
      "namespace": "notifications"
    },

    // E-mail footer literals
    "footer": {
        "text": "Population services international (PSI)"
    },

    // E-mail SMTP configuration
    "smtp": {
        "host": "smtp.gmail.com",
        "port": 465,
        "auth": {
            "user": "user@gmail.com",
            "pass": "password"
        }
    }
}
```

## Commands examples

Send emails to subscribers of objects (charts, eventCharts, maps, reportTables, eventReports):

```
$ dhis2-subscriptions [-c path/to/config.json] send-notifications
```

Send a weekly report of interpretations to subscribers of their parent objects:

```
$ dhis2-subscriptions [-c path/to/config.json] send-newsletters
```
