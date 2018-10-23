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

You may use the script from a crontab entry. An example using our `cronwrap` (see `crontab/` folder) to check limits every six hours:

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
    $HOME/toggl/toggl_alerts.rb \
    --workspace=EyeSeeTea-Android \
    --tag=Maintenance \
    --limit-hours=60 \
    --email-recipients=user1@server.org,user2@server.org \
    --thresholds=50,90,100 \
    --api-token-path=$HOME/toggl/est-android-token.txt \
    --email-from="info@eyeseetea.com"
```
