# ESTools: Check for Unmonitored Services

This script is designed to verify whether certain services monitored by `monit` on a Linux system are no longer actively monitored. If any of these services are not monitored for a certain period, the script sends a notification via a configured webhook.
Its mainly purpose is to notify the user to avoid leaving some services as unmonitored after maintenance periods.

## Requirements

- Linux operating system with `monit` installed and configured.
- Python installed for the `webhook_notifier.py` script.
- Able to execute `monit` to retrieve information about the services status (usually requires to be run as root).
- Internet connection to send webhook notifications (can be used through a proxy)

## Installation

1. Clone this repository on your server:

    ```bash
    git clone https://github.com/EyeSeeTea/ESTools.git
    cd ESTools/monitoring/check_unmonitored

2. Make sure the scripts have execution permissions:

    ```bash
    chmod +x check_unmonitor.sh alert_unmonitor.sh

## Usage

The scripts will perform the following actions:

- Retrieve from `monit` all unmonitored services, filtered by name according to `-i <regex>` to include and `-e <regex>` to exclude.
- Get when was the last time the service was monitored and filter out services that are not monitored for some time.
- If an unmonitored service is found, a notification will be sent to the configured webhook.

Main logic is in `check_unmonitor.sh` whereas `alert_unmonitor.sh` is a wrapper for that script that will send the notification using `webhook_notifier.py`.
You may use `check_unmonitor.sh` at any time to get the list of unmonitored services without sending any notification.
`alert_unmonitor.sh` is expected to be run periodically, so typical usage would be including in a crontab:

```bash
0 * * * * /ESTools/monitoring/check_unmonitored/alert_unmonitor.sh > /var/log/alert_unmonitor.log


## Webhook Configuration

Before running the script, edit the alert_unmonitor.sh file and set the WEBHOOK_URL variable to your webhook URL:

    ```bash
    WEBHOOK_URL="https://your-webhook-url.com"

you may also change other details like the proxy configuration or other details like the time it waits before sending an alert or what regex to filter the service names
