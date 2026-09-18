#!/usr/bin/env python3
"""
Lists the DHIS2 apps installed in an apps directory (name + version from each
folder's manifest), warns when two folders contain an app with the same name,
and keeps a history CSV of when each app/version was detected or removed.
duplicates.csv always holds the current duplicates and only changes when they do.

The apps directory is only read, never modified.

Usage:
    python3 dhis2_app_audit.py --apps-dir /path/files/apps [--data-dir .]
"""

import argparse
import csv
import io
import json
import os
import sys
import time

os.environ["TZ"] = "Europe/Madrid"
time.tzset()

HISTORY_FILE = "history.csv"
COLUMNS = ["date", "event", "folder", "name", "version", "folder_date"]
DUPLICATES_FILE = "duplicates.csv"
DUPLICATE_COLUMNS = ["name", "folder", "version"]


def timestamp(epoch=None):
    """Same format as `TZ=Europe/Madrid date --rfc-3339=seconds`."""
    t = time.localtime(epoch)
    tz = time.strftime("%z", t)
    return time.strftime("%Y-%m-%d %H:%M:%S", t) + tz[:3] + ":" + tz[3:]


def log(msg):
    print("[%s] %s" % (timestamp(), msg), file=sys.stderr)


def read_manifest(folder_path):
    """Return (name, version) from manifest.webapp, or manifest.json as fallback."""
    for filename in ("manifest.webapp", "manifest.json"):
        path = os.path.join(folder_path, filename)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8-sig") as f:
                data = json.load(f)
            return str(data.get("name") or ""), str(data.get("version") or "")
        except Exception as e:
            log("WARNING: cannot read %s: %s" % (path, e))
    return "", ""


def scan(apps_dir):
    """Return {(folder, name, version): folder_date} for every app folder."""
    apps = {}
    for folder in sorted(os.listdir(apps_dir)):
        path = os.path.join(apps_dir, folder)
        if not os.path.isdir(path):
            continue
        name, version = read_manifest(path)
        apps[(folder, name, version)] = timestamp(os.path.getmtime(path))
    return apps


def load_known(history_path):
    """Replay the history to get the apps present at the last run."""
    known = {}
    if not os.path.exists(history_path):
        return known
    with open(history_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = (row["folder"], row["name"], row["version"])
            if row["event"] == "DETECTED":
                known[key] = row["folder_date"]
            else:
                known.pop(key, None)
    return known


def write_if_changed(path, rows):
    """Write rows as CSV only if the content differs from the existing file."""
    buffer = io.StringIO()
    csv.writer(buffer).writerows(rows)
    content = buffer.getvalue()
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as f:
            if f.read() == content:
                return
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    log("%s updated (%d duplicated folders)" % (path, len(rows) - 1))


def main():
    parser = argparse.ArgumentParser(description="DHIS2 apps inventory and history.")
    parser.add_argument("--apps-dir", required=True, help="DHIS2 apps directory (read only)")
    parser.add_argument("--data-dir", default=".", help="where history.csv and duplicates.csv are kept (default: current dir)")
    args = parser.parse_args()

    if not os.path.isdir(args.apps_dir):
        log("ERROR: apps directory does not exist: %s" % args.apps_dir)
        sys.exit(1)

    os.makedirs(args.data_dir, exist_ok=True)
    history_path = os.path.join(args.data_dir, HISTORY_FILE)
    current = scan(args.apps_dir)
    known = load_known(history_path)

    # Guard: an empty apps dir (e.g. during a redeploy) would mark everything REMOVED.
    if not current and known:
        log("ERROR: no apps found in %s but the history has apps; not updating history"
            % args.apps_dir)
        sys.exit(1)

    now = timestamp()
    changes = []
    for key in sorted(set(current) - set(known)):
        changes.append(["DETECTED", key, current[key]])
    for key in sorted(set(known) - set(current)):
        changes.append(["REMOVED", key, known[key]])

    if changes:
        new_file = not os.path.exists(history_path)
        with open(history_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(COLUMNS)
            for event, (folder, name, version), folder_date in changes:
                writer.writerow([now, event, folder, name, version, folder_date])
                log("%s %s: %s %s" % (event, folder, name, version))
    else:
        log("No changes (%d apps)" % len(current))

    # Duplicates: same app name in more than one folder.
    apps_by_name = {}
    for key in current:
        if key[1]:
            apps_by_name.setdefault(key[1].lower(), []).append(key)
    duplicates = []
    for name, keys in sorted(apps_by_name.items()):
        if len(keys) > 1:
            log("DUPLICATE '%s' in: %s"
                % (name, ", ".join("%s (%s)" % (k[0], k[2]) for k in sorted(keys))))
            for folder, app_name, version in sorted(keys):
                duplicates.append([app_name, folder, version])

    # duplicates.csv holds the current duplicates only and is rewritten only when
    # they change, so a change in this file means new or resolved duplicates.
    write_if_changed(os.path.join(args.data_dir, DUPLICATES_FILE),
                     [DUPLICATE_COLUMNS] + duplicates)


if __name__ == "__main__":
    main()

