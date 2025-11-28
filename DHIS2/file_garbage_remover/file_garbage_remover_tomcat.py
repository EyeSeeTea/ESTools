#!/usr/bin/env python3
import argparse
import os
import shutil
import sys
from datetime import datetime

import psycopg2

from common import (
    build_datavalue_items,
    build_document_items,
    emit_summary,
    load_config,
    log,
    mark_items_notified,
)
from csv_utils import deduplicate_items, append_items
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


def get_events(cursor):
    cursor.execute(SQL_EVENT_FILE_UIDS)
    return [row[0] for row in cursor.fetchall() if row[0]]


def get_event_blob(cursor):
    event_texts = get_events(cursor)
    return "\n".join(json.dumps(e) for e in event_texts)


def get_all_datavalue_uids(cursor):
    cursor.execute(SQL_DATA_VALUE_UIDS)
    return set(row[0] for row in cursor.fetchall() if row[0])


def get_all_tracker_uids(cursor):
    cursor.execute(SQL_TRACKER_ATTRIBUTE_UIDS)
    return set(row[0] for row in cursor.fetchall() if row[0])


def get_matching_files(storage_key, base_dir, folder):
    # Folder (document or dataValue)
    storage_key = storage_key.replace(folder + "/", "")
    base_dir = os.path.join(base_dir, folder)
    matching = []
    for filename in os.listdir(base_dir):
        if filename.startswith(storage_key):
            fullpath = os.path.join(base_dir, filename)
            if os.path.isfile(fullpath):
                matching.append(fullpath)
    return matching


def update_db(fileresourceid, cursor, conn, dry_run=False):
    if dry_run:
        log("[DRY RUN] Would execute:")
        log(f"  {SQL_INSERT_AUDIT.strip()}")
        log(f"  with parameters: {{'fid': '{fileresourceid}'}}")
        log(f"  {SQL_DELETE_ORIGINAL.strip()} ")
        log(f"  with parameters: {{'fid': '{fileresourceid}'}}")
    else:
        try:
            cursor.execute(SQL_INSERT_AUDIT, {"fid": fileresourceid})
            cursor.execute(SQL_DELETE_ORIGINAL, {"fid": fileresourceid})
            conn.commit()
            log(f"Archived and deleted fileresourceid {fileresourceid}")
        except Exception as e:
            log(f"❌ Failed DB update for fileresourceid {fileresourceid}: {e}")
            conn.rollback()
            raise


def move_files(file_list, file_base_path, temp_file_path, folder, dry_run):
    base_dir = os.path.join(file_base_path, folder)
    dest_dir = os.path.join(temp_file_path, folder)
    for src in file_list:
        rel_path = os.path.relpath(src, base_dir)
        log(rel_path)
        dst = os.path.join(dest_dir, rel_path)
        log(dst)
        dst_dir = os.path.dirname(dst)
        log(dst_dir)
        try:
            os.makedirs(dst_dir, exist_ok=True)
        except Exception as e:
            log(f"❌ Failed to create directory {dst_dir}: {e}")
            raise

        log(f"{'[DRY RUN] ' if dry_run else ''}Moving {src} -> {dst}")
        if not dry_run:
            try:
                shutil.move(src, dst)
            except Exception as e:
                log(f"❌ Failed to move {src}: {e}")
                raise


def ensure_audit_table_exists(cursor, dry_run=False):
    if dry_run:
        log("[DRY RUN] Would execute:")
        log(SQL_CREATE_TABLE_IF_NOT_EXIST)
    else:
        log("Ensuring 'fileresourcesaudit' table exists...")
        cursor.execute(SQL_CREATE_TABLE_IF_NOT_EXIST)
        log("'fileresourcesaudit' table ready.")


def main():
    parser = argparse.ArgumentParser(description="Move orphaned DHIS2 file resources and archive DB entries.")
    parser.add_argument("--force", action="store_true", help="Apply changes: move files and modify DB.")
    parser.add_argument("--test", action="store_true", help="Run in dry-run mode (no changes). Default if --force not provided.")
    parser.add_argument("--config", required=True, help="Path to config.json file.")
    parser.add_argument("--csv-path", help="Optional CSV file to record processed entries.")
    parser.add_argument("--save-all-as-notified", action="store_true", help="Store CSV entries with notified=true even if not sent.")
    args = parser.parse_args()

    config = load_config(args.config)
    required_keys = ["db_host", "db_port", "db_name", "db_user", "file_base_path", "temp_file_path"]
    missing_keys = [k for k in required_keys if not config.get(k)]

    if missing_keys:
        log(f"❌ Missing required config keys: {', '.join(missing_keys)}")
        sys.exit(1)

    db_password = os.environ.get("DB_PASSWORD_FG")
    if not db_password:
        log("❌ Missing required environment variable: DB_PASSWORD_FG")
        sys.exit(1)

    db_url = f"postgresql://{config['db_user']}:{db_password}@{config['db_host']}:{config['db_port']}/{config['db_name']}"
    file_base_path = config["file_base_path"]
    temp_file_path = config["temp_file_path"]

    if not os.path.isdir(file_base_path) or not os.path.isdir(temp_file_path):
        log("❌ Both 'file_base_path' and 'temp_file_path' must exist and be directories.")
        log(f"    file_base_path: {file_base_path} -> {'OK' if os.path.isdir(file_base_path) else 'INVALID'}")
        log(f"    temp_file_path: {temp_file_path} -> {'OK' if os.path.isdir(temp_file_path) else 'INVALID'}")
        sys.exit(1)

    if args.force and args.test:
        log("❌ Choose either --force or --test, not both.")
        sys.exit(1)

    dry_run = not args.force  # default to test mode unless --force is provided
    log(f"{'Running in TEST mode' if dry_run else 'Running in FORCE mode'}")
    log(f"Connecting to database: {db_url}")
    log(f"File base path: {file_base_path}")
    log(f"Temporary move path: {temp_file_path}")

    summary = {"mode": "TEST" if dry_run else "FORCE", "items": []}

    with psycopg2.connect(dsn=db_url) as conn:
        with conn.cursor() as cur:
            ensure_audit_table_exists(cur, dry_run)
            remove_documents(file_base_path, temp_file_path, dry_run, cur, conn, summary)
            remove_datavalues(file_base_path, temp_file_path, dry_run, cur, conn, summary)

    if args.csv_path:
        if args.save_all_as_notified:
            mark_items_notified(summary.get("items", []))
        else:
            merge_notified_flags(args.csv_path, summary.get("items", []), unique_keys=("id", "uid"), log=log)
        items = deduplicate_items(args.csv_path, summary.get("items", []), unique_keys=("id", "uid"), overwrite=False, log=log)
        append_items(args.csv_path, items, overwrite=False, log=log)
    emit_summary(summary.get("items", []), summary.get("mode", "TEST"), log_fn=log)


def remove_documents(file_base_path, temp_file_path, dry_run, cur, conn, summary):
    log("Querying orphaned fileresource entries...")
    cur.execute(SQL_FIND_ORPHANS_DOCUMENTS)
    raw_rows = cur.fetchall()
    items = build_document_items(raw_rows)

    if not items:
        log("✅ No orphaned fileresource entries found.")
        return

    log(f"Found {len(items)} \"document\" orphaned entries.")
    process_orphan_items(items, file_base_path, temp_file_path, dry_run, cur, conn, summary)


def remove_datavalues(file_base_path, temp_file_path, dry_run, cur, conn, summary):
    log("Querying orphaned fileresource entries...")
    cur.execute(SQL_FIND_DATA_VALUES_FILE_RESOURCES)
    raw_rows = cur.fetchall()
    # get all file resource datavalues
    datavalue_uids = get_all_datavalue_uids(cur)
    # get all events with file dataelement values
    event_blob = get_event_blob(cur)

    tracker_uids = get_all_tracker_uids(cur)
    items = build_datavalue_items(raw_rows, datavalue_uids, tracker_uids, event_blob)

    if not items:
        log("✅ No fileResources entries found.")
        return

    log(f"Found {len(items)} \"data_value\" orphaned entries.")
    process_orphan_items(items, file_base_path, temp_file_path, dry_run, cur, conn, summary)


def process_orphan_items(orphan_items, file_base_path, temp_file_path, dry_run, cur, conn, summary):
    count = 0
    for item in orphan_items:
        fileresourceid = item.get("id")
        storagekey = item.get("storagekey", "")
        name = item.get("name", "")
        folder = item.get("folder", "")
        if not fileresourceid:
            log(f"⚠️ Skipping row with empty/null fileresourceid: {fileresourceid}")
            continue
        try:
            matches = get_matching_files(storagekey, file_base_path, folder)
            if not matches:
                log(f"No files found for storage_key: {storagekey} (folder={folder})")
            else:
                move_files(matches, file_base_path, temp_file_path, folder, dry_run)
            # Always update the db also if the files not existed on disk
            update_db(fileresourceid, cur, conn, dry_run)
            rel_matches = [os.path.join(folder, os.path.relpath(m, os.path.join(file_base_path, folder))) for m in matches]
            item["files"] = rel_matches
            item["action"] = "would_move_and_delete" if dry_run else "moved_and_deleted"
            summary["items"].append(item)
        except Exception as e:
            log(f"❌ Aborting due to error with fileresourceid {fileresourceid}: {e}")
            sys.exit(1)
        count = count + 1
    log(f"{count} file(s) {'would be moved' if dry_run else 'were successfully moved and deleted'}")


if __name__ == "__main__":
    main()
