#!/usr/bin/env python3
import argparse
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
    parser.add_argument("--save-all-as-notified", action="store_true", help="Mark CSV entries as notified even if no notification is sent.")
    parser.add_argument("--notify-max-lines", type=int, default=100, help="Maximum number of lines to include in notification content (default 100).")

    return parser


def resolve_webhook(config_path, cli_webhook):
    return cli_webhook or _from_config(config_path, ["webhook-url", "webhook_url"])


def _from_config(config_path, keys):
    if not config_path:
        return None
    try:
        cfg = cleaner.load_config(config_path)
    except Exception as e:
        print(f"❌ Failed to load config file: {e}", file=sys.stderr)
        sys.exit(1)
    for key in keys:
        if key in cfg:
            return cfg.get(key)
    return None


def resolve_proxy(config_path, cli_value, keys):
    return cli_value or _from_config(config_path, keys)


def run_notify_flow(csv_path, config_path=None, webhook_url=None, title=None, http_proxy=None, https_proxy=None, notify_test=False, notify_max_lines=50):
    names, ids, fieldnames, rows = pending_from_csv(csv_path)
    if not names and not save_all_as_notified:
        return
    max_lines = notify_max_lines if notify_max_lines and notify_max_lines > 0 else None
    truncated = names[:max_lines] if max_lines else names
    content = "\n".join(truncated)
    if max_lines and len(names) > max_lines:
        content += f"\n... (truncated {len(names) - max_lines} more)"
    webhook = resolve_webhook(config_path, webhook_url)
    http_proxy = resolve_proxy(config_path, http_proxy, ["notify-http-proxy", "notify_http_proxy", "http-proxy", "http_proxy"])
    https_proxy = resolve_proxy(config_path, https_proxy, ["notify-https-proxy", "notify_https_proxy", "https-proxy", "https_proxy"])
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
    # mark entries as notified
    ids_to_mark = ids if not save_all_as_notified else set(str(row.get("id")) for row in rows)
    if ids_to_mark:
        mark_notified(csv_path, rows, fieldnames, ids_to_mark)


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
            notify_max_lines=args.notify_max_lines,
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
    if args.save_all_as_notified:
        return #nothing to report
    elif wants_notify:
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
            notify_max_lines=args.notify_max_lines,
        )


if __name__ == "__main__":
    main()
