#!/usr/bin/env python3
import argparse
import json
import sys

import cleaner
from notifier import mark_notified, pending_from_csv, send_notification


def build_parser():
    parser = argparse.ArgumentParser(description="DHIS2 file garbage remover and notifier.")
    # Cleanup options
    parser.add_argument("--force", action="store_true", help="Apply changes: move files and modify DB.")
    parser.add_argument("--test", action="store_true", help="Run in dry-run mode (default unless --force).")
    parser.add_argument("--config", help="Path to config.json file. Required unless --notify-only.")
    parser.add_argument("--csv-path", help="CSV file to record processed entries or to read notifications from.")
    parser.add_argument("--maintain-csv", action="store_true", help="Keep CSV contents even in --force mode (append only).")
    parser.add_argument("--mode", choices=["tomcat", "docker"], default="tomcat", help="Cleanup mode: tomcat (default) or docker.")
    parser.add_argument("--docker-instance", help="d2-docker instance name (required for --mode=docker).")

    # Notification options
    parser.add_argument("--notify-only", action="store_true", help="Skip cleanup and only send notifications from CSV.")
    parser.add_argument("--notify-webhook-url", help="Webhook URL to send the notification. If not provided, falls back to config.json key 'webhook-url'.")
    parser.add_argument("--notify-title", help="Notification title (required if using --notify-webhook-url).")
    parser.add_argument("--notify-http-proxy", help="HTTP proxy (optional).")
    parser.add_argument("--notify-https-proxy", help="HTTPS proxy (optional).")
    parser.add_argument("--notify-test", action="store_true", help="Dry-run notification: print payload instead of sending.")

    return parser


def resolve_webhook(config_path, cli_webhook):
    if cli_webhook:
        return cli_webhook
    if not config_path:
        return None
    try:
        cfg = cleaner.load_config(config_path)
    except Exception as e:
        print(f"❌ Failed to load config file: {e}", file=sys.stderr)
        sys.exit(1)
    return cfg.get("webhook-url") or cfg.get("webhook_url")


def run_notify_flow(csv_path, config_path=None, webhook_url=None, title=None, http_proxy=None, https_proxy=None, notify_test=False):
    names, ids, fieldnames, rows = pending_from_csv(csv_path)
    if not names:
        return
    content = "\n".join(names)
    webhook = resolve_webhook(config_path, webhook_url)
    if notify_test:
        print(f"[TEST] Would send notification to {webhook or '<no-webhook-configured>'}")
        print(f"[TEST] Title: {title or '<no-title>'}")
        print(f"[TEST] Content:\n{content}")
    if webhook:
        if not title:
            print("❌ --notify-title is required when using --notify-webhook-url", file=sys.stderr)
            sys.exit(1)
        if not notify_test:
            try:
                send_notification(
                    webhook_url=webhook,
                    title=title,
                    content=content,
                    http_proxy=http_proxy,
                    https_proxy=https_proxy,
                )
            except Exception as e:
                print(f"❌ Failed to send notification: {e}", file=sys.stderr)
                sys.exit(1)
    else:
        for name in names:
            print(name)
    mark_notified(csv_path, rows, fieldnames, ids)


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Notify-only path
    if args.notify_only:
        if not args.csv_path:
            print("❌ --csv-path is required for notify-only mode", file=sys.stderr)
            sys.exit(1)
        run_notify_flow(
            csv_path=args.csv_path,
            config_path=args.config,
            webhook_url=args.notify_webhook_url,
            title=args.notify_title,
            http_proxy=args.notify_http_proxy,
            https_proxy=args.notify_https_proxy,
            notify_test=args.notify_test,
        )
        sys.exit(0)

    # Cleanup path (default)
    if not args.config:
        print("❌ --config is required to run cleanup", file=sys.stderr)
        sys.exit(1)
    cleaner.run_cleanup(args)

    wants_notify = any([
        args.notify_webhook_url,
        args.notify_title,
        args.notify_http_proxy,
        args.notify_https_proxy,
        args.notify_test,
    ])
    if wants_notify:
        if not args.csv_path:
            print("❌ --csv-path is required to send notifications after cleanup", file=sys.stderr)
            sys.exit(1)
        run_notify_flow(
            csv_path=args.csv_path,
            config_path=args.config,
            webhook_url=args.notify_webhook_url,
            title=args.notify_title,
            http_proxy=args.notify_http_proxy,
            https_proxy=args.notify_https_proxy,
            notify_test=args.notify_test,
        )


if __name__ == "__main__":
    main()
