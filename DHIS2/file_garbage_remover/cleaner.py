#!/usr/bin/env python3
import json
import os
import re
import shutil
import sys
from datetime import datetime

import subprocess
import psycopg2

from common import load_config, log, mark_items_notified
from csv_utils import append_items, deduplicate_items, merge_notified_flags
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
    storage_key = storage_key.replace(folder + "/", "")
    base_dir = os.path.join(base_dir, folder)
    if not os.path.isdir(base_dir):
        log(f"⚠️ Skipping search: base directory does not exist: {base_dir}")
        return []
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
        dst = os.path.join(dest_dir, rel_path)
        dst_dir = os.path.dirname(dst)
        os.makedirs(dst_dir, exist_ok=True)
        log(f"{'[DRY RUN] ' if dry_run else ''}Moving {src} -> {dst}")
        if not dry_run:
            shutil.move(src, dst)


def ensure_audit_table_exists(cursor, dry_run=False):
    if dry_run:
        log("[DRY RUN] Would execute:")
        log(SQL_CREATE_TABLE_IF_NOT_EXIST)
    else:
        log("Ensuring 'fileresourcesaudit' table exists...")
        cursor.execute(SQL_CREATE_TABLE_IF_NOT_EXIST)
        log("'fileresourcesaudit' table ready.")


def remove_documents(file_base_path, temp_file_path, dry_run, cur, conn, summary):
    log("Querying orphaned fileresource entries (documents)...")
    cur.execute(SQL_FIND_ORPHANS_DOCUMENTS)
    rows = cur.fetchall()
    if not rows:
        log("✅ No orphaned fileresource entries found (documents).")
        return
    log(f"Found {len(rows)} \"document\" orphaned entries.")
    process_orphan_files(rows, file_base_path, temp_file_path, dry_run, cur, conn, "document", summary)


def remove_datavalues(file_base_path, temp_file_path, dry_run, cur, conn, summary):
    log("Querying orphaned fileresource entries (data values)...")
    cur.execute(SQL_FIND_DATA_VALUES_FILE_RESOURCES)
    rows = cur.fetchall()

    datavalue_uids = get_all_datavalue_uids(cur)
    event_blob = get_event_blob(cur)
    tracker_uids = get_all_tracker_uids(cur)

    orphan_data_values = []
    for fileresourceid, uid, storagekey, name, created in rows:
        if uid in datavalue_uids:
            continue  # Referenced in datavalue
        if uid in event_blob:
            continue  # Referenced in event
        if uid in tracker_uids:
            continue  # Referenced in a tracker attribute
        orphan_data_values.append((fileresourceid, storagekey, name, created))

    if not orphan_data_values:
        log("✅ No fileResources entries found (data values).")
        return

    log(f"Found {len(orphan_data_values)} \"data_value\" orphaned entries.")
    process_orphan_files(orphan_data_values, file_base_path, temp_file_path, dry_run, cur, conn, "dataValue", summary)


def process_orphan_files(orphan_data_values, file_base_path, temp_file_path, dry_run, cur, conn, folder, summary):
    count = 0
    for entry in orphan_data_values:
        fileresourceid, storagekey = entry[0], entry[1]
        name = entry[2] if len(entry) > 2 else ""
        created = entry[3] if len(entry) > 3 else None
        if not fileresourceid:
            log(f"⚠️ Skipping row with empty/null fileresourceid: {fileresourceid}")
            continue
        matches = get_matching_files(storagekey, file_base_path, folder)
        if not matches:
            log(f"No files found for storage_key: {storagekey} (folder={folder})")
        else:
            move_files(matches, file_base_path, temp_file_path, folder, dry_run)
        update_db(fileresourceid, cur, conn, dry_run)
        rel_matches = [os.path.join(folder, os.path.relpath(m, os.path.join(file_base_path, folder))) for m in matches]
        summary["items"].append({
            "id": fileresourceid,
            "name": name,
            "storagekey": storagekey,
            "folder": folder,
            "files": rel_matches,
            "created": created.isoformat() if hasattr(created, "isoformat") else created,
            "detection_date": datetime.utcnow().isoformat(),
            "action": "would_move_and_delete" if dry_run else "moved_and_deleted",
            "notified": False
        })
        count += 1
    log(f"{count} file(s) {'would be moved' if dry_run else 'were successfully moved and deleted'}")


def emit_summary(summary):
    mode = summary.get("mode", "TEST")
    items = summary.get("items", [])
    log(f"Summary ({mode}): {len(items)} fileresource entries processed.")
    for item in items:
        files = item.get("files") or ["<missing from disk>"]
        log(f"  - id={item.get('id')} name=\"{item.get('name')}\" storagekey={item.get('storagekey')} action={item.get('action')}")
        for f in files:
            log(f"      file: {f}")


def run_cleanup(args):
    if args.mode == "docker":
        run_docker_cleanup(args)
        return

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

    dry_run = not args.force
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
        if getattr(args, "save_all_as_notified", False):
            mark_items_notified(summary.get("items", []))
        else:
            merge_notified_flags(args.csv_path, summary.get("items", []), unique_keys=("id", "uid"), log=log)
        items = deduplicate_items(args.csv_path, summary.get("items", []), unique_keys=("id", "uid"), overwrite=False, log=log)
        append_items(args.csv_path, items, overwrite=False, log=log)
    emit_summary(summary)


def run_docker_cleanup(args):
    if not args.docker_instance:
        log("❌ --docker-instance is required when --mode=docker")
        sys.exit(1)
    script_path = os.path.join(os.path.dirname(__file__), "file_garbage_remover_docker.py")
    if not os.path.isfile(script_path):
        log(f"❌ Docker cleanup script not found at {script_path}")
        sys.exit(1)
    cmd = [sys.executable, script_path, "--instance", args.docker_instance]
    if args.csv_path:
        cmd.extend(["--csv-path", args.csv_path])
        if getattr(args, "save_all_as_notified", False):
            cmd.append("--save-all-as-notified")
    if args.force:
        cmd.append("--force")
    log(f"Running docker cleanup via: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        log(f"❌ Docker cleanup failed: {e}")
        sys.exit(e.returncode)
