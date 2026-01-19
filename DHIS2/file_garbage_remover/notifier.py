#!/usr/bin/env python3
import os
import sys
import requests

from csv_utils import read_rows, write_rows


def pending_from_csv(csv_path):
    rows, fieldnames = read_rows(csv_path)

    notify_ids = set()
    names_to_print = []
    for row in rows:
        notified = str(row.get("notified", "")).lower() == "true"
        if notified:
            continue
        name = row.get("name", "")
        if name:
            names_to_print.append(name)
        notify_ids.add(str(row.get("id")))

    return names_to_print, notify_ids, fieldnames, rows


def mark_notified(csv_path, rows, fieldnames, notify_ids):
    if not notify_ids:
        return
    for row in rows:
        if str(row.get("id")) in notify_ids:
            row["notified"] = "true"
    write_rows(csv_path, rows, fieldnames=fieldnames)


def send_notification(webhook_url, title, content, http_proxy=None, https_proxy=None):
    proxies = {
        "http": http_proxy or os.getenv("http_proxy", ""),
        "https": https_proxy or os.getenv("https_proxy", "")
    }
    payload = {"text": f"**{title}**\n{content}"}
    response = requests.post(
        webhook_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        proxies=proxies,
        verify=True,
        timeout=10,
    )
    response.raise_for_status()
    return response.status_code


def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    csv_path = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else None
    names, ids, fieldnames, rows = pending_from_csv(csv_path, days)
    if not names:
        sys.exit(1)
    for name in names:
        print(name)
    mark_notified(csv_path, rows, fieldnames, ids)
    sys.exit(0)


if __name__ == "__main__":
    main()
