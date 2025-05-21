#!/usr/bin/env python3

import subprocess
import sys
import argparse


LOCAL_SQL_FILE = "/tmp/find_orphan_files.sql"
LOCAL_LIST_FILE = "/tmp/list_of_files_to_be_removed.txt"
REMOTE_LIST_FILE = "/tmp/list_of_files_to_be_removed.txt"
FILE_BASE_PATH = "/DHIS2_home/files"


SQL_QUERY = """
    SELECT storagekey
    FROM fileresource fr
    WHERE NOT EXISTS (
        SELECT 1 FROM document d WHERE d.fileresource = fr.fileresourceid
    )
    AND fr.uid NOT IN (
        SELECT url FROM document
    )
    AND fr.domain = 'DOCUMENT';
"""


def run(command, check=True, capture=False):
    """Run a shell command."""
    print(f"$ {' '.join(command)}")
    return subprocess.run(command, check=check, capture_output=capture, text=True)


def find_container_id(name_pattern):
    """Find the container ID based on a name substring."""
    result = run(["docker", "ps", "--format", "{{.ID}}\t{{.Names}}"], capture=True)
    for line in result.stdout.strip().splitlines():
        cid, name = line.split("\t")
        if name_pattern in name:
            return cid
    return None


def slugify(instance_name):
    """Convert instance name to container name slug."""
    return "d2-docker-" + instance_name.replace("/", "-").replace(":", "-").replace(".", "-")


def main():
    parser = argparse.ArgumentParser(description="Remove orphaned DHIS2 file resources from Core container.")
    parser.add_argument("-i", "--instance", required=True, help="d2-docker instance name (e.g. /usr/bin/python3 file_garbage_remover.py -i docker.eyeseetea.com/widpit/dhis2-data:2.42-widp-preprod-cont-indiv)")
    args = parser.parse_args()

    instance_name = args.instance
    container_slug = slugify(instance_name)
    db_container_match = container_slug + "-db-1"
    core_container_match = container_slug + "-core-1"

    print("Writing SQL file...")
    with open(LOCAL_SQL_FILE, "w") as f:
        f.write(SQL_QUERY)

    print("Running SQL with d2-docker and capturing output...")
    result = run(["d2-docker", "run-sql", "-i", instance_name, LOCAL_SQL_FILE], capture=True)

    print("Saving result to file...")
    with open(LOCAL_LIST_FILE, "w") as f:
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if line and not line.lower().startswith("storagekey"):
                f.write(f"{line}\n")

    print("Identifying containers...")
    db_container = find_container_id(db_container_match.replace("dhis2-data-", ""))
    core_container = find_container_id(core_container_match.replace("dhis2-data-",""))
    print(db_container)
    print(core_container)
    if not db_container or not core_container:
        print("Could not find DB or Core container.")
        print(f"Looked for: {db_container_match}, {core_container_match}")
        sys.exit(1)

    print(f"DB container: {db_container}")
    print(f"Core container: {core_container}")

    print("Copying file list to Core container...")
    run(["docker", "cp", LOCAL_LIST_FILE, f"{core_container}:{REMOTE_LIST_FILE}"])

    print(f"Deleting orphaned files in Core container... {core_container} {db_container_match}")
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

    run(["docker", "exec", core_container, "bash", "-c", delete_cmd])

    print("Cleanup complete.")


if __name__ == "__main__":
    main()
