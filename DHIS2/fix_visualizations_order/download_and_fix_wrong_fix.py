#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DHIS2 visualization fetch + period-order fixer (compact)

- Reads UIDs from a CSV (first column).
- Fetches each visualization via /api/visualizations/{uid}.json?fields=*,rows[*].
- Fixes 'pe' (period) rows by sorting 4-digit years ascending while keeping non-year tokens at the end.
- Writes two pretty JSON files:
  * original_output{suffix}.json  (as downloaded)
  * fixed_output{suffix}.json     (after normalization)
"""

import csv
import json
import re
import sys
from typing import Any, Dict, List, Optional
import requests
from pathlib import Path
from copy import deepcopy

# =========================
# CONFIG
# =========================

suffix = "_dev"
UIDS_CSV_PATH = f"errors{suffix}.csv"

OUTPUT_JSON_MOD = f"fixed_output{suffix}.json"      # fixed
OUTPUT_JSON_ORIG = f"original_output{suffix}.json"  # as-is

BASE_URL = "https://server/dhis2"

# Hardcoded JSESSIONID
JSESSIONID_VALUE = ""

REQUEST_TIMEOUT = 30
NUMERIC_YEAR_RE = re.compile(r"^\d{4}$")


def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Accept": "application/json",
        "User-Agent": "simple-dhis2-fixer/1.0",
    })
    s.cookies.set("JSESSIONID", JSESSIONID_VALUE)
    return s


def load_uids(csv_path: str) -> List[str]:
    uids: List[str] = []
    p = Path(csv_path)
    if not p.is_file():
        print(f"[ERROR] UIDs CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    with p.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue
            uid = row[0].strip()
            if not uid:
                continue
            if i == 0 and uid.lower() in {"uid", "uids", "id"}:
                continue
            uids.append(uid)
    return uids


def fetch_visualization(session: requests.Session, base_url: str, uid: str, timeout: int) -> Optional[Dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/api/visualizations/{uid}.json?fields=*,rows[*]"
    print(f"📡 GET: {url}")
    try:
        r = session.get(url, timeout=timeout)
    except requests.RequestException as e:
        print(f"[ERROR] {uid}: network error -> {e}", file=sys.stderr)
        return None

    if r.status_code != 200:
        print(f"[ERROR] {uid}: HTTP {r.status_code} -> {r.text[:200]}", file=sys.stderr)
        return None

    try:
        return r.json()
    except ValueError:
        print(f"[ERROR] {uid}: response is not JSON. Snippet: {r.text[:200]}", file=sys.stderr)
        return None


def reorder_years(ids: List[str]) -> List[str]:
    numeric = [x for x in ids if NUMERIC_YEAR_RE.match(x)]
    non_numeric = [x for x in ids if not NUMERIC_YEAR_RE.match(x)]
    return sorted(numeric, key=lambda x: int(x)) + non_numeric


def fix_pe_rows(viz: Dict[str, Any]) -> bool:
    rows = viz.get("rows")
    if not isinstance(rows, list):
        return False

    changed = False
    for row in rows:
        if isinstance(row, dict) and row.get("dimension") == "pe":
            items = row.get("items", [])
            if not isinstance(items, list) or not items:
                continue
            ids = [str(it.get("id")) for it in items if isinstance(it, dict) and "id" in it]
            if not ids:
                continue
            expected = reorder_years(ids)
            if ids != expected:
                original_map = {str(it.get("id")): it for it in items if "id" in it}
                row["items"] = [original_map.get(i, {"id": i}) for i in expected]
                changed = True
    return changed


def main():
    session = build_session()
    uids = load_uids(UIDS_CSV_PATH)
    print(f"Processing {len(uids)} UIDs...\n")

    originals: List[Dict[str, Any]] = []
    modifieds: List[Dict[str, Any]] = []
    changed_count = 0
    missing_count = 0

    for uid in uids:
        viz = fetch_visualization(session, BASE_URL, uid, REQUEST_TIMEOUT)
        if viz is None:
            missing_count += 1
            continue

        originals.append(deepcopy(viz))

        fixed_viz = deepcopy(viz)
        if fix_pe_rows(fixed_viz):
            changed_count += 1
        modifieds.append(fixed_viz)

    with open(OUTPUT_JSON_ORIG, "w", encoding="utf-8") as f:
        json.dump({"count": len(originals), "visualizations": originals}, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_JSON_MOD, "w", encoding="utf-8") as f:
        json.dump({"count": len(modifieds), "visualizations": modifieds}, f, ensure_ascii=False, indent=2)

    print("\nSummary")
    print(f"  Total UIDs           : {len(uids)}")
    print(f"  Visualizations OK    : {len(modifieds) - changed_count}")
    print(f"  Reordered            : {changed_count}")
    print(f"  Not downloaded (err) : {missing_count}")
    print(f"\nOriginal output  : {OUTPUT_JSON_ORIG}")
    print(f"Fixed output     : {OUTPUT_JSON_MOD}")


if __name__ == "__main__":
    main()
