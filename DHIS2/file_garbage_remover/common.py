import json
import os
import re
from datetime import datetime


def log(message):
    """Simple logger with timestamp and DB URL password masking."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(message, str):
        message = re.sub(
            r"(postgresql://[^:]+:)([^@]+)(@)",
            r"\1*****\3",
            message
        )
    print(f"[{timestamp}] {message}")


def load_config(path):
    with open(path, "r") as f:
        return json.load(f)


def mark_items_notified(items):
    for item in items:
        item["notified"] = True


def emit_summary(items, mode, log_fn=print):
    log_fn(f"Summary ({mode}): {len(items)} fileresource entries processed.")
    for item in items:
        files = item.get("files") or ["<missing from disk>"]
        log_fn(f"  - id={item.get('id')} name=\"{item.get('name')}\" storagekey={item.get('storagekey')} action={item.get('action')}")
        for f in files:
            log_fn(f"      file: {f}")


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def build_document_items(raw_rows):
    items = []
    for fid, uid, storagekey, name, created in raw_rows:
        items.append({
            "id": fid,
            "uid": uid,
            "name": name,
            "storagekey": storagekey,
            "folder": "document",
            "files": [],
            "created": _iso(created),
            "detection_date": datetime.utcnow().isoformat(),
            "action": "would_move_and_delete",
            "notified": False,
        })
    return items


def build_datavalue_items(raw_rows, datavalue_uids, tracker_uids, event_blob):
    items = []
    for fid, uid, storagekey, name, created in raw_rows:
        if uid in datavalue_uids:
            continue
        if uid in event_blob:
            continue
        if uid in tracker_uids:
            continue
        items.append({
            "id": fid,
            "uid": uid,
            "name": name,
            "storagekey": storagekey,
            "folder": "dataValue",
            "files": [],
            "created": _iso(created),
            "detection_date": datetime.utcnow().isoformat(),
            "action": "would_move_and_delete",
            "notified": False,
        })
    return items
