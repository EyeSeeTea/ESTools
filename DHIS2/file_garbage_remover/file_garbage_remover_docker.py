#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import tempfile
from datetime import datetime

from csv_utils import append_items, deduplicate_items, merge_notified_flags
from common import (
    build_datavalue_items,
    build_document_items,
    emit_summary,
    mark_items_notified,
)
from sql_queries import (
    SQL_CREATE_TABLE_IF_NOT_EXIST,
    SQL_DATA_VALUE_UIDS,
    SQL_DELETE_ORIGINAL,
    SQL_EVENT_FILE_UIDS,
    SQL_FIND_DATA_VALUES_FILE_RESOURCES,
    SQL_FIND_ORPHANS_DOCUMENTS,
    SQL_INSERT_AUDIT,
    SQL_TRACKER_ATTRIBUTE_UIDS,
)


def run(cmd, capture=False):
    kwargs = {"check": True}
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
        kwargs["text"] = True
    return subprocess.run(cmd, **kwargs)


def find_container_id(instance):
    slug = "d2-docker-" + instance.replace("/", "-").replace(":", "-").replace(".", "-")
    core = slug.replace("dhis2-data-", "") + "-core-1"
    result = run(["docker", "ps", "--format", "{{.ID}}", "-f", f"name={core}"], capture=True)
    lines = result.stdout.strip().splitlines()
    if not lines:
        return None
    return lines[0]


def run_sql(instance, sql):
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(sql)
        tmp_path = f.name
    try:
        result = run(["d2-docker", "run-sql", "-i", instance, tmp_path], capture=True)
        return result.stdout
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def parse_tab_rows(output, expected_cols):
    rows = []
    for line in output.strip().splitlines():
        if not line or line.lower().startswith("fileresourceid") or line.lower().startswith("value") or line.lower().startswith("eventdatavalues"):
            continue
        if line.startswith("(") and "row" in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < expected_cols:
            continue
        rows.append(parts)
    return rows


def get_orphan_documents(instance):
    out = run_sql(instance, SQL_FIND_ORPHANS_DOCUMENTS)
    raw_rows = parse_tab_rows(out, 5)
    return build_document_items(raw_rows)


def get_orphan_datavalues(instance):
    data_rows = parse_tab_rows(run_sql(instance, SQL_FIND_DATA_VALUES_FILE_RESOURCES), 5)
    datavalue_uids = set(r[0] for r in parse_tab_rows(run_sql(instance, SQL_DATA_VALUE_UIDS), 1))
    tracker_uids = set(r[0] for r in parse_tab_rows(run_sql(instance, SQL_TRACKER_ATTRIBUTE_UIDS), 1))
    event_blob = "\n".join(r[0] for r in parse_tab_rows(run_sql(instance, SQL_EVENT_FILE_UIDS), 1))
    return build_datavalue_items(data_rows, datavalue_uids, tracker_uids, event_blob)


def delete_files(container_id, row, dry_run):
    base = "/DHIS2_home/files"
    storagekey = row["storagekey"]
    folder = row["folder"]
    prefix = os.path.join(base, folder, storagekey.replace(f"{folder}/", ""))
    cmd = ["docker", "exec", container_id, "bash", "-c", f"rm -v {prefix}*"]
    if dry_run:
        print(f"[DRY RUN] {' '.join(cmd)}")
    else:
        try:
            run(cmd)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  File deletion failed (likely missing): {' '.join(cmd)} -> {e}")
            # Continue with DB cleanup and CSV logging even if file is already gone.


def ensure_audit_table(instance):
    run_sql(instance, SQL_CREATE_TABLE_IF_NOT_EXIST)


def archive_and_delete(instance, fileresourceid):
    fid = int(fileresourceid)
    sql = (SQL_INSERT_AUDIT % {"fid": fid}) + (SQL_DELETE_ORIGINAL % {"fid": fid})
    run_sql(instance, sql)


def main():
    parser = argparse.ArgumentParser(description="Find/delete orphan file resources in d2-docker instance and log to CSV.")
    parser.add_argument("--instance", required=True, help="d2-docker instance name (e.g. docker.eyeseetea.com/project/dhis2-data:2.41-test)")
    parser.add_argument("--csv-path", help="CSV file to log orphan entries.")
    parser.add_argument("--force", action="store_true", help="Actually delete files in container.")
    parser.add_argument("--save-all-as-notified", action="store_true", help="Store CSV entries with notified=true even if not sent.")
    args = parser.parse_args()

    container_id = find_container_id(args.instance)
    if not container_id:
        print("❌ Could not find core container for instance", file=sys.stderr)
        sys.exit(1)

    dry_run = not args.force
    print(f"Running in {'DRY-RUN' if dry_run else 'FORCE'} mode against container {container_id}")

    ensure_audit_table(args.instance)

    rows = []
    rows.extend(get_orphan_documents(args.instance))
    rows.extend(get_orphan_datavalues(args.instance))
    print(f"Found {len(rows)} orphan entries")

    if args.save_all_as_notified:
        mark_items_notified(rows)
    else:
        if args.csv_path:
            merge_notified_flags(args.csv_path, rows, unique_keys=("id", "uid"))

    for row in rows:
        delete_files(container_id, row, dry_run)
        if dry_run:
            print(f"[DRY RUN] Skipping DB archive/delete for {row['id']} ({row.get('name', '')}) action={row.get('action')}")
            continue
        try:
            archive_and_delete(args.instance, row["id"])
            row["action"] = "moved_and_deleted"
        except Exception as e:
            print(f"❌ Failed DB archive/delete for {row['id']}: {e}", file=sys.stderr)
            if not dry_run:
                sys.exit(1)

    if args.csv_path:
        items = deduplicate_items(args.csv_path, rows, unique_keys=("id", "uid"), overwrite=False)
        append_items(args.csv_path, items, overwrite=False)

    emit_summary(rows, "DRY-RUN" if dry_run else "FORCE", log_fn=print)


if __name__ == "__main__":
    main()
