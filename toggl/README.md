## Toggl Alerts

Features:

- Send an email at the start of the last full week of a month.
- Send an email whenever a defined threshold is reached (multiple thresholds can be configured)

### Setup

Select a Ruby with `rvm` and install the dependencies:

```
$ rvm use 2.5.1
$ bundle install
```

Configure your API token and metadata in [toggl_alerts.json](toggl_alerts.json).

You typically will use the script from a crontab entry. An example using a simple cron wrapper (see `crontab/` folder) to check limits every six hours:

```
0 */6  * * * /usr/local/bin/toggl-alarms.sh
```

```
#!/bin/bash
set -e -u
# /usr/local/bin/toggl-alarms.sh

/usr/local/bin/cronwrap \
    $HOME/toggl/alerts.log \
    $HOME/.rvm/wrappers/ruby-2.5.1/ruby \
    $HOME/toggl/toggl_alerts.rb
```
