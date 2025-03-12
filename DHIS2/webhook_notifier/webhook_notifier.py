#!/usr/bin/env python3

import argparse
import requests
import os

def send_notification(webhook_url, title, content, http_proxy, https_proxy):
    proxies = {
        "http": http_proxy or os.getenv("http_proxy", ""),
        "https": https_proxy or os.getenv("https_proxy", "")
    }

    payload = {"text": f"**{title}**\n{content}"}
    try:
        response = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, proxies=proxies, verify=True)
        response.raise_for_status()
        print(f"[OK] Notification sent: {response.status_code}")
    except requests.RequestException as e:
        print(f"[ERROR] Failed to send notification: {e}")

def main():
    parser = argparse.ArgumentParser(description="Send a notification to a webhook")
    parser.add_argument("--webhook-url", required=True, help="The webhook URL to send the notification to")
    parser.add_argument("--title", required=True, help="Notification title")
    parser.add_argument("--content", required=True, help="Notification content")
    parser.add_argument("--http-proxy", help="HTTP proxy (optional)")
    parser.add_argument("--https-proxy", help="HTTPS proxy (optional)")

    args = parser.parse_args()

    send_notification(
        webhook_url=args.webhook_url,
        title=args.title,
        content=args.content,
        http_proxy=args.http_proxy,
        https_proxy=args.https_proxy
    )

if __name__ == "__main__":
    main()