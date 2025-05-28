# Continuous Analytics Fixer
This script monitors DHIS2 servers for delayed continuous analytics tasks and attempts to restart them if necessary.

# Usage
Run the script:

`python3 continous_analytics_fixer.py`
Ensure that a config.json file is present in the same directory with the required configuration.

Configuration (config.json)
Example format:

json
```
{
    "user_master": "admin",
    "password_master": "password",
    "threshold_seconds": 600,
    "webhook_url": "https://example.com/webhook",
    "http_proxy": "",
    "https_proxy": "",
    "servers": [
        {
            "name": "Server1",
            "url": "https://server1.example.com",
            "user": "admin",
            "password": "password"
        }
    ]
}
```

# How It Works
Loads configuration from config.json.
Iterates through the list of servers and checks their analytics scheduler.

If a Continuous Analytics Task is scheduled but delayed beyond the defined threshold:

If the task is not running, attempts to restart it and send alert via webhook.