#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime

import psycopg2

SQL_FIND_ORPHANS_DOCUMENTS = """
    SELECT fileresourceid, storagekey, name, created
    FROM fileresource fr
    WHERE NOT EXISTS (
        SELECT 1 FROM document d WHERE d.fileresource = fr.fileresourceid
    )
    AND fr.uid NOT IN (
        SELECT url FROM document
    )
    AND fr.domain = 'DOCUMENT' and  fr.storagekey like '%document%';
"""

SQL_FIND_DATA_VALUES_FILE_RESOURCES = """
    SELECT fileresourceid, uid, storagekey, name, created
    FROM fileresource fr where fr.domain = 'DATA_VALUE' and  fr.storagekey like '%dataValue%';
"""

SQL_INSERT_AUDIT = """
    INSERT INTO fileresourcesaudit SELECT * FROM fileresource WHERE fileresourceid = %(fid)s;
"""

SQL_DELETE_ORIGINAL = """
    DELETE FROM fileresource WHERE fileresourceid = %(fid)s;
"""

SQL_CREATE_TABLE_IF_NOT_EXIST = """
    CREATE TABLE IF NOT EXISTS fileresourcesaudit AS TABLE fileresource WITH NO DATA;
"""

SQL_EVENT_FILE_UIDS = """
        SELECT eventdatavalues
        FROM event
        WHERE programstageid 
        IN (SELECT programstageid FROM programstagedataelement WHERE dataelementid  
        IN (SELECT dataelementid FROM dataelement WHERE valuetype='FILE_RESOURCE' or valuetype='IMAGE')) and deleted='f';
"""

SQL_DATA_VALUE_UIDS = """
        SELECT dv.value
        FROM datavalue dv
        WHERE dv.value IN (SELECT uid FROM fileresource WHERE domain='DATA_VALUE')
"""

SQL_TRACKER_ATTRIBUTE_UIDS = """
select value from trackedentityattributevalue where value IN (SELECT uid FROM fileresource WHERE domain='DATA_VALUE');
"""


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(message, str):
        # Detect pattern like: postgresql://user:password@host
        message = re.sub(
            r"(postgresql://[^:]+:)([^@]+)(@)",
            r"\1*****\3",
            message
        )
    print(f"[{timestamp}] {message}")


def load_config(path):
    with open(path, "r") as f:
        return json.load(f)


def get_events(cursor):
    cursor.execute(SQL_EVENT_FILE_UIDS)
    return [row[0] for row in cursor.fetchall() if row[0]]


def get_event_blob(cursor):
    event_texts = get_events(cursor)
    return "\n".join(json.dumps(e) for e in event_texts)


def get_data_value_file_resources(cursor):
    cursor.execute("""
        SELECT fileresourceid, uid, storagekey
        FROM fileresource
        WHERE domain = 'DATA_VALUE'
    """)
    return cursor.fetchall()


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
    parser.add_argument("--csv-path", help="Optional CSV file to record processed entries. In --force mode the file is rewritten unless --maintain-csv.")
    parser.add_argument("--maintain-csv", action="store_true", help="Keep CSV contents even in --force mode (append only).")
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
        overwrite_csv = bool(args.force) and not args.maintain_csv
        write_csv(args.csv_path, summary, overwrite=overwrite_csv)
    emit_summary(summary)


def remove_documents(file_base_path, temp_file_path, dry_run, cur, conn, summary):
    log("Querying orphaned fileresource entries...")
    cur.execute(SQL_FIND_ORPHANS_DOCUMENTS)
    rows = cur.fetchall()

    if not rows:
        log("✅ No orphaned fileresource entries found.")
        return

    log(f"Found {len(rows)} \"document\" orphaned entries.")
    process_orphan_files(rows, file_base_path, temp_file_path, dry_run, cur, conn, "document", summary)


def remove_datavalues(file_base_path, temp_file_path, dry_run, cur, conn, summary):
    log("Querying orphaned fileresource entries...")
    cur.execute(SQL_FIND_DATA_VALUES_FILE_RESOURCES)
    rows = cur.fetchall()

    # get all file resource datavalues
    datavalue_uids = get_all_datavalue_uids(cur)
    # get all events with file dataelement values
    event_blob = get_event_blob(cur)

    tracker_uids = get_all_tracker_uids(cur)
    # 3. Filter out referenced file resources
    orphan_data_values = []
    for fileresourceid, uid, storagekey, name, created in rows:
        if uid in datavalue_uids:
            continue  # Referenced in datavalue
        if uid in event_blob:
            continue  # Referenced in event
        if uid in tracker_uids:
            continue # referenced in a trackerentityattribute
        orphan_data_values.append((fileresourceid, storagekey, name, created))

    if not orphan_data_values:
        log("✅ No fileResources entries found.")
        return

    log(f"Found {len(orphan_data_values)} \"data_value\" orphaned entries.")
    process_orphan_files(orphan_data_values, file_base_path, temp_file_path, dry_run, cur, conn, "dataValue", summary)


def process_orphan_files(orphan_data_values, file_base_path, temp_file_path, dry_run, cur, conn, folder, summary):
    count = 0
    for entry in orphan_data_values:
        # entries may come as (id, storagekey, name)
        fileresourceid, storagekey = entry[0], entry[1]
        name = entry[2] if len(entry) > 2 else ""
        created = entry[3] if len(entry) > 3 else None
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
            summary["items"].append({
                "id": fileresourceid,
                "name": name,
                "storagekey": storagekey,
                "folder": folder,
                "files": rel_matches,
                "created": created.isoformat() if hasattr(created, "isoformat") else created,
                "action": "would_move_and_delete" if dry_run else "moved_and_deleted",
                "notified": False
            })
        except Exception as e:
            log(f"❌ Aborting due to error with fileresourceid {fileresourceid}: {e}")
            sys.exit(1)
        count = count + 1
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


def write_csv(csv_path, summary, overwrite=False):
    if not csv_path:
        return
    file_exists = os.path.isfile(csv_path)
    mode = "w" if overwrite else "a"
    want_header = overwrite or not file_exists
    fieldnames = ["id", "name", "created", "storagekey", "folder", "action", "files", "notified"]
    existing_ids = set()
    if not overwrite and file_exists:
        try:
            with open(csv_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "id" in row and row["id"]:
                        existing_ids.add(str(row["id"]))
        except Exception as e:
            log(f"⚠️ Could not read existing CSV for deduplication: {e}")
    try:
        with open(csv_path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if want_header:
                writer.writeheader()
            for item in summary.get("items", []):
                if str(item.get("id")) in existing_ids:
                    continue
                writer.writerow({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "created": item.get("created"),
                    "storagekey": item.get("storagekey"),
                    "folder": item.get("folder"),
                    "action": item.get("action"),
                    "files": "|".join(item.get("files") or []),
                    "notified": str(item.get("notified", False)).lower(),
                })
        log(f"CSV summary {'overwritten' if overwrite else 'appended'} at {csv_path}")
    except Exception as e:
        log(f"❌ Failed to write CSV {csv_path}: {e}")


if __name__ == "__main__":
    main()
