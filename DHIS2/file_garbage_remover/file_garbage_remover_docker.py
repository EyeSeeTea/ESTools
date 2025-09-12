#!/usr/bin/env python3

"""Remove orphaned DHIS2 file resources from a d2-docker instance.

This script mimics the behaviour of ``file_garbage_remover_tomcat.py`` but
operates on instances managed by `d2-docker`. It detects orphaned file
resources (both ``DOCUMENT`` and ``DATA_VALUE`` domains) and either prints the
actions that would be taken (``--test``) or actually removes the files and
archives/deletes the database entries (``--force``).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from typing import Iterable, List, Sequence, Tuple


LOCAL_LIST_FILE = "/tmp/list_of_files_to_be_removed.txt"
REMOTE_LIST_FILE = "/tmp/list_of_files_to_be_removed.txt"
FILE_BASE_PATH = "/DHIS2_home/files"

SQL_FIND_ORPHANS_DOCUMENTS = """
    SELECT fileresourceid, storagekey
    FROM fileresource fr
    WHERE NOT EXISTS (
        SELECT 1 FROM document d WHERE d.fileresource = fr.fileresourceid
    )
    AND fr.uid NOT IN (
        SELECT url FROM document
    )
    AND fr.domain = 'DOCUMENT' and fr.storagekey like '%document%';
"""

SQL_FIND_DATA_VALUES_FILE_RESOURCES = """
    SELECT fileresourceid, uid, storagekey
    FROM fileresource fr where fr.domain = 'DATA_VALUE' and fr.storagekey like '%dataValue%';
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

SQL_CREATE_TABLE_IF_NOT_EXIST = """
    CREATE TABLE IF NOT EXISTS fileresourcesaudit AS TABLE fileresource WITH NO DATA;
"""


def run(command: Sequence[str], capture: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and echo it to stdout."""

    print(f"$ {' '.join(command)}")
    return subprocess.run(command, check=check, capture_output=capture, text=True)


def slugify(instance_name: str) -> str:
    """Convert instance name to container name slug."""

    return "d2-docker-" + instance_name.replace("/", "-").replace(":", "-").replace(".", "-")


def find_container_id(name_pattern: str) -> str | None:
    """Return the first container ID matching ``name_pattern`` or ``None``."""

    result = run(["docker", "ps", "--format", "{{.ID}}", "-f", f"name={name_pattern}"], capture=True)
    lines = result.stdout.strip().splitlines()
    return lines[0] if lines else None


def run_sql(instance: str, sql: str, parse: bool = True) -> List[str]:
    """Execute ``sql`` in the given instance and optionally parse the output."""

    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(sql)
        tmp_path = tmp.name

    try:
        result = run(["d2-docker", "run-sql", "-i", instance, tmp_path], capture=True)
    finally:
        os.unlink(tmp_path)

    if not parse:
        return []

    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]

    # Drop header if present
    if lines and any(c.isalpha() for c in lines[0]):
        lines = lines[1:]

    return lines


def parse_pairs(lines: Iterable[str]) -> List[Tuple[str, str]]:
    """Parse ``fileresourceid storagekey`` pairs."""

    pairs: List[Tuple[str, str]] = []
    for ln in lines:
        parts = ln.split()
        if len(parts) >= 2:
            pairs.append((parts[0], parts[1]))
    return pairs


def parse_triples(lines: Iterable[str]) -> List[Tuple[str, str, str]]:
    """Parse ``fileresourceid uid storagekey`` triples."""

    triples: List[Tuple[str, str, str]] = []
    for ln in lines:
        parts = ln.split()
        if len(parts) >= 3:
            triples.append((parts[0], parts[1], parts[2]))
    return triples


def get_document_orphans(instance: str) -> List[Tuple[str, str]]:
    return parse_pairs(run_sql(instance, SQL_FIND_ORPHANS_DOCUMENTS))


def get_data_value_orphans(instance: str) -> List[Tuple[str, str]]:
    rows = parse_triples(run_sql(instance, SQL_FIND_DATA_VALUES_FILE_RESOURCES))
    datavalue_uids = set(run_sql(instance, SQL_DATA_VALUE_UIDS))
    event_blob = "\n".join(run_sql(instance, SQL_EVENT_FILE_UIDS))
    tracker_uids = set(run_sql(instance, SQL_TRACKER_ATTRIBUTE_UIDS))

    orphans: List[Tuple[str, str]] = []
    for fid, uid, storagekey in rows:
        if uid in datavalue_uids:
            continue
        if uid in event_blob:
            continue
        if uid in tracker_uids:
            continue
        orphans.append((fid, storagekey))

    return orphans


def update_db(instance: str, fileresource_ids: Sequence[str], dry_run: bool) -> None:
    if not fileresource_ids:
        return

    id_list = ",".join(fileresource_ids)
    script = (
        f"{SQL_CREATE_TABLE_IF_NOT_EXIST}\n"
        f"INSERT INTO fileresourcesaudit SELECT * FROM fileresource WHERE fileresourceid IN ({id_list});\n"
        f"DELETE FROM fileresource WHERE fileresourceid IN ({id_list});\n"
    )

    if dry_run:
        print("[DRY RUN] Would execute SQL:")
        print(script)
    else:
        run_sql(instance, script, parse=False)


def delete_files(container: str, storage_keys: Sequence[str], dry_run: bool) -> None:
    if not storage_keys:
        return

    with open(LOCAL_LIST_FILE, "w") as f:
        for key in storage_keys:
            f.write(f"{key}\n")

    if dry_run:
        print("[DRY RUN] Would delete the following files:")
        for key in storage_keys:
            print(f"  {key}")
        return

    run(["docker", "cp", LOCAL_LIST_FILE, f"{container}:{REMOTE_LIST_FILE}"])

    delete_cmd = f"""
    bash -c '
    if [ ! -f "{REMOTE_LIST_FILE}" ]; then
        echo "File list not found: {REMOTE_LIST_FILE}"
        exit 1
    fi

    while IFS= read -r key; do
        fullpath="{FILE_BASE_PATH}/$key"
        echo "Deleting files: $fullpath*"
        rm -v "$fullpath"* 2>/dev/null || echo "Nothing to delete for $fullpath"
    done < "{REMOTE_LIST_FILE}"
    '
    """

    run(["docker", "exec", container, "bash", "-c", delete_cmd])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove orphaned DHIS2 file resources from a d2-docker instance."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--test", action="store_true", help="Run in dry-run mode (no changes)."
    )
    group.add_argument(
        "--force", action="store_true", help="Apply changes: delete files and update DB."
    )
    parser.add_argument(
        "-i",
        "--instance",
        required=True,
        help="d2-docker instance name (e.g. docker.repo/project/dhis2-data:tag)",
    )
    args = parser.parse_args()

    dry_run = args.test
    instance = args.instance
    container_slug = slugify(instance)
    core_container_match = container_slug.replace("dhis2-data-", "") + "-core-1"
    core_container = find_container_id(core_container_match)
    print(f"Core container: {core_container}")

    documents = get_document_orphans(instance)
    datavalues = get_data_value_orphans(instance)
    all_orphans = documents + datavalues

    if not all_orphans:
        print("No orphaned fileresources found.")
        return

    print(f"Found {len(all_orphans)} orphaned fileresources.")

    ids = [fid for fid, _ in all_orphans]
    keys = [key for _, key in all_orphans]

    update_db(instance, ids, dry_run)
    delete_files(core_container, keys, dry_run)

    print(
        f"{len(keys)} file(s) {'would be deleted' if dry_run else 'were deleted and DB entries archived'}"
    )


if __name__ == "__main__":
    main()

