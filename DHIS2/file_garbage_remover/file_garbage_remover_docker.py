#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import tempfile
from datetime import datetime

from csv_utils import append_items, deduplicate_items

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

SQL_INSERT_AUDIT = """
    INSERT INTO fileresourcesaudit SELECT * FROM fileresource WHERE fileresourceid = {fid};
"""

SQL_DELETE_ORIGINAL = """
    DELETE FROM fileresource WHERE fileresourceid = {fid};
"""

SQL_CREATE_TABLE_IF_NOT_EXIST = """
    CREATE TABLE IF NOT EXISTS fileresourcesaudit AS TABLE fileresource WITH NO DATA;
"""


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
    rows = []
    for fid, storagekey, name, created in parse_tab_rows(out, 4):
        rows.append({
            "id": fid,
            "name": name,
            "storagekey": storagekey,
            "folder": "document",
            "files": [],
            "created": created,
            "detection_date": datetime.utcnow().isoformat(),
            "action": "would_move_and_delete",
            "notified": False,
        })
    return rows


def get_orphan_datavalues(instance):
    data_rows = parse_tab_rows(run_sql(instance, SQL_FIND_DATA_VALUES_FILE_RESOURCES), 5)
    datavalue_uids = set(r[0] for r in parse_tab_rows(run_sql(instance, SQL_DATA_VALUE_UIDS), 1))
    tracker_uids = set(r[0] for r in parse_tab_rows(run_sql(instance, SQL_TRACKER_ATTRIBUTE_UIDS), 1))
    event_blob = "\n".join(r[0] for r in parse_tab_rows(run_sql(instance, SQL_EVENT_FILE_UIDS), 1))

    orphans = []
    for fid, uid, storagekey, name, created in data_rows:
        if uid in datavalue_uids:
            continue
        if uid in event_blob:
            continue
        if uid in tracker_uids:
            continue
        orphans.append({
            "id": fid,
            "name": name,
            "storagekey": storagekey,
            "folder": "dataValue",
            "files": [],
            "created": created,
            "detection_date": datetime.utcnow().isoformat(),
            "action": "would_move_and_delete",
            "notified": False,
        })
    return orphans


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
    sql = SQL_INSERT_AUDIT.format(fid=fid) + SQL_DELETE_ORIGINAL.format(fid=fid)
    run_sql(instance, sql)


def main():
    parser = argparse.ArgumentParser(description="Find/delete orphan file resources in d2-docker instance and log to CSV.")
    parser.add_argument("--instance", required=True, help="d2-docker instance name (e.g. docker.eyeseetea.com/project/dhis2-data:2.41-test)")
    parser.add_argument("--csv-path", help="CSV file to log orphan entries.")
    parser.add_argument("--force", action="store_true", help="Actually delete files in container.")
    parser.add_argument("--maintain-csv", action="store_true", help="Append to CSV in force mode (do not overwrite).")
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
        overwrite_csv = bool(args.force) and not args.maintain_csv
        items = deduplicate_items(args.csv_path, rows, unique_keys=("id", "name"), overwrite=overwrite_csv)
        append_items(args.csv_path, items, overwrite=overwrite_csv)

    print(f"Summary: processed {len(rows)} orphan entries")


if __name__ == "__main__":
    main()
