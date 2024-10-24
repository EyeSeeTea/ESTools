# check_user_usergroup_size

This script is designed to monitor changes in users and user groups on a DHIS2 server. Its primary goal is to detect cache issues and notify when they have been resolved. Additionally, it handles legitimate changes in user groups and updates the data accordingly.

## How does the script work?

### Configuration loading

At the beginning, the script reads a configuration file that provides DHIS2 server credentials, including the server, username, and password.

### Creating the initial comparison file

If the `last_values.json` file does not exist, the script requests the current state of users and their groups from the server and saves it to this file. This ensures that there is always an initial state for future comparisons.

### Avoiding false positives

By filtering common users, the script ensures that any detected differences between the states are not due to new or removed users, but rather reflect actual changes in the user groups of existing users. This reduces the likelihood of false positives when detecting cache issues.

### Detecting recent changes in user groups

The script checks if there have been updates in the `userGroups` in the last 5 minutes. If recent changes are detected, the script ends as it doesn’t make sense to proceed if the user groups are being modified.

### State comparison

If no recent changes are found, the script compares the current state of users with the last saved state in `last_values.json`. If differences are detected, it could indicate a cache issue.

### Cache cleaning

If changes are detected, the script clears the DHIS2 server cache to see if this resolves the issue. After waiting for 30 seconds, it fetches the user data again.

### Post-cache cleaning verification

After cleaning the cache, the script compares the states again. If the issue is resolved (i.e., it was a cache issue), the new corrected state is saved, and the `control_file.json` is updated with the cache issue detection date.

### Handling legitimate changes

If the changes are not related to a cache issue, the script saves the new state without further modifications.

## What files does the script manage?

- **last_values.json**: Stores the last known state of users and their user groups for future comparisons.
- **control_file.json**: Stores the date when a cache issue was identified and resolved. This is used by Monit to trigger notifications.

## How to run the script

To execute the script, you need to pass the `--config` parameter followed by the path to the configuration file:

`python check_user_usergroup_size.py --config file.json`
