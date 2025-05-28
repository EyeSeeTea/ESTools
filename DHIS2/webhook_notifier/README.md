# Webhook Notifier
This script sends notifications to a webhook URL.

# Usage
Run the script with the following parameters:

python3 notification_sender.py --webhook-url URL --title "Title" --content "Message"
Parameters:
--webhook-url: The webhook URL to send the notification to (required).
--title: Notification title (required).
--content: Notification message (required).
--http-proxy: Optional HTTP proxy.
--https-proxy: Optional HTTPS proxy.

# How It Works
Parses command-line arguments.
Sends a POST request with the message to the webhook.
Displays whether the notification was successfully sent or if an error occurred.


# Requirements
Python 3
requests module (pip install requests)