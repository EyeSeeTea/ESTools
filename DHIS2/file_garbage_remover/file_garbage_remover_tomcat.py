#!/usr/bin/env python3
import re

import psycopg2
import shutil
import os
import argparse
import json
import sys
from datetime import datetime

SQL_FIND_ORPHANS = """
    SELECT fileresourceid, storagekey
    FROM fileresource fr
    WHERE NOT EXISTS (
        SELECT 1 FROM document d WHERE d.fileresource = fr.fileresourceid
    )
    AND fr.uid NOT IN (
        SELECT url FROM document
    )
    AND fr.domain = 'DOCUMENT' and  fr.storagekey like '%document%';
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

def get_matching_document_files(storage_key, base_dir):
    storage_key = storage_key.replace("document/", "")
    base_dir = os.path.join(base_dir, "document")
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

def move_files(file_list, file_base_path, temp_file_path, dry_run=False):
    base_dir = os.path.join(file_base_path, "document")
    dest_dir = os.path.join(temp_file_path, "document")
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
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", action="store_true", help="Run in dry-run mode (no changes).")
    group.add_argument("--force", action="store_true", help="Apply changes: move files and modify DB.")
    parser.add_argument("--config", required=True, help="Path to config.json file.")
    args = parser.parse_args()

    config = load_config(args.config)
    required_keys = ["db_host", "db_port", "db_name", "db_user", "file_base_path", "temp_file_path"]
    missing_keys = [k for k in required_keys if not config.get(k)]

    if missing_keys:
        log(f"❌ Missing required config keys: {', '.join(missing_keys)}")
        sys.exit(1)

    db_password = os.environ.get("DB_PASSWORD_FILE_G")
    if not db_password:
        log("❌ Missing required environment variable: DB_PASSWORD")
        sys.exit(1)

    db_url = f"postgresql://{config['db_user']}:{db_password}@{config['db_host']}:{config['db_port']}/{config['db_name']}"
    file_base_path = config["file_base_path"]
    temp_file_path = config["temp_file_path"]

    if not os.path.isdir(file_base_path) or not os.path.isdir(temp_file_path):
        log("❌ Both 'file_base_path' and 'temp_file_path' must exist and be directories.")
        log(f"    file_base_path: {file_base_path} -> {'OK' if os.path.isdir(file_base_path) else 'INVALID'}")
        log(f"    temp_file_path: {temp_file_path} -> {'OK' if os.path.isdir(temp_file_path) else 'INVALID'}")
        sys.exit(1)

    dry_run = args.test
    log(f"{'Running in TEST mode' if dry_run else 'Running in FORCE mode'}")
    log(f"Connecting to database: {db_url}")
    log(f"File base path: {file_base_path}")
    log(f"Temporary move path: {temp_file_path}")

    with psycopg2.connect(dsn=db_url) as conn:
        with conn.cursor() as cur:
            ensure_audit_table_exists(cur, dry_run)
            log("Querying orphaned fileresource entries...")
            cur.execute(SQL_FIND_ORPHANS)
            rows = cur.fetchall()

            if not rows:
                log("✅ No orphaned fileresource entries found.")
                return

            log(f"Found {len(rows)} orphaned entries.")
            count = 0
            for fileresourceid, storagekey in rows:
                if not fileresourceid:
                    log(f"⚠️ Skipping row with empty/null fileresourceid: {fileresourceid}")
                    continue

                try:
                    matches = get_matching_document_files(storagekey, file_base_path)
                    if not matches:
                        raise Exception(f"No files found for storage_key: {storagekey}")
                    move_files(matches, file_base_path, temp_file_path, dry_run)
                    update_db(fileresourceid, cur, conn, dry_run)
                except Exception as e:
                    log(f"❌ Aborting due to error with fileresourceid {fileresourceid}: {e}")
                    sys.exit(1)
                count = count + 1
            log(f"{count} file(s) {'would be moved' if dry_run else 'were successfully moved and deleted'}")

if __name__ == "__main__":
    main()
