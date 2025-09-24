# Notify expiration
This script searches for users that will have their password expired, log it and cand send a simplified notification to a webhook URL.

# Usage
Run the script with the following parameters:

python3 notify_expiration.py --config <file.json> (--debug)
Parameters:
--config <file>: Mandatory configuration file where the URL, credentials and other parameters are configured
--debug: Optional parameter to ask for debugging logs, to ensure proper load of the configuration file and all details regarding data gathered and filtered.

# Config file
It accepts the following attributes as a json:
- `server`: Mandatory. The url of the DHIS2 instance. Should end with a slash `/`, but it will append it if not present.
- `user`: Mandatory. The user needed to authenticate to the instance.
- `password`: Mandatory. The password for the authentication.
- `filterGroup`: Optional. Defaults to `None`. An array of userGroup names to be considered as the only ones to evaluate. It allows to restrict the result to those who belong to any of these groups instead of the whole DHIS instance.
- `months_expiry`: Optional. Defaults to `18`. Should reflect the actual password policy of the instance. It does not retrieve the value from the instance as this allows to evaluate instances without an active password expiration policy.
- `how_many_days`: Optional. Defaults to `7`. As this script was conceived to be run periodically notifying which users will have their password expiring in the current week.
- `pnly_enabled`: Optional. Defaults to `true`. When set to `true`, restricts the evaluation to enabled users. When set to false it will evaluate both enabled and disable users.
- `webhook_url`: Optional. Defaults to `""`. If empty, will not send any notification and will only present the data directly in the console. If set to an URL, it will use it to notify the list of users (with expiration date and if they are disabled). This endpoint should expect to receive a json with 2 parameters: `text` and `dest`. `text` will be compossed with a `title` in bold followed by the content of the notification. `dest` should be used to determine the `destination` of the notification.
- `title`: Optional. Defaults to `"DHIS2 Password Expiration Notification"`. Allows to set a custom title to the notification.
- `destination`: Optional. Defaults to `"sysadmin"`. Allows the webhook URL to select the correct destination of the notification.
- `http_proxy`: Optional. If not present, will try to use an environmental variable of the same name. If present will be used for the webhook notification.
- `https_proxy`: Optional. If not present, will try to use an environmental variable of the same name. If present will be used for the webhook notification.

# How It Works
Parses config file.
Sends a GET request to retrieve the list of all users and some attributes needed to determine when the user is going to expire
Displays what users are in the expected range of dates and optionally sends a notification via webhook, as well as details of it was successful.

# Requirements
Python 3
requests module (pip install requests)