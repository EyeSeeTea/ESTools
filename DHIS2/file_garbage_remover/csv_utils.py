import csv
import os

DEFAULT_FIELDNAMES = ["id", "name", "created", "detection_date", "storagekey", "folder", "action", "files", "notified"]


def serialize_item(item):
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "created": item.get("created"),
        "detection_date": item.get("detection_date"),
        "storagekey": item.get("storagekey"),
        "folder": item.get("folder"),
        "action": item.get("action"),
        "files": "|".join(item.get("files") or []),
        "notified": str(item.get("notified", False)).lower(),
    }


def append_items(csv_path, items, overwrite=False, log=None):
    """
    Append serialized items to CSV. If overwrite=True, start fresh.
    """
    mode = "w" if overwrite else "a"
    file_exists = os.path.isfile(csv_path)
    want_header = overwrite or not file_exists
    try:
        with open(csv_path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=DEFAULT_FIELDNAMES)
            if want_header:
                writer.writeheader()
            for item in items:
                writer.writerow(serialize_item(item))
        if log:
            log(f"CSV summary {'overwritten' if overwrite else 'appended'} at {csv_path}")
    except Exception as e:
        if log:
            log(f"❌ Failed to write CSV {csv_path}: {e}")
        else:
            raise


def read_rows(csv_path):
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or DEFAULT_FIELDNAMES
        rows = list(reader)
    return rows, fieldnames


def write_rows(csv_path, rows, fieldnames=None):
    fieldnames = fieldnames or DEFAULT_FIELDNAMES
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def deduplicate_items(csv_path, new_items, unique_keys=("id",), overwrite=False, log=None):
    """
    Returns new_items filtered to avoid duplicates with existing CSV based on unique_keys.
    If overwrite=True, no filtering is applied (CSV will be rewritten).
    """
    if overwrite or not os.path.isfile(csv_path):
        return new_items

    existing_keys = set()
    try:
        rows, _ = read_rows(csv_path)
        for row in rows:
            key = tuple((row.get(k) or "").strip() for k in unique_keys)
            existing_keys.add(key)
    except Exception as e:
        if log:
            log(f"⚠️ Could not read existing CSV for deduplication: {e}")

    filtered = []
    for item in new_items:
        key = tuple((str(item.get(k)) or "").strip() for k in unique_keys)
        if key in existing_keys:
            continue
        existing_keys.add(key)
        filtered.append(item)
    return filtered
