#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DHIS2 period-order checker (minimal version)

What it does
------------
- Loads visualizations from: visualizations_check{SUFIX}.json (in the same folder as this script)
- For each visualization, finds the 'pe' dimension under 'rows' and reads its item IDs
- Considers these valid:
    * Strict ascending years (e.g., 2013 2014 2015)
    * Strict descending years (e.g., 2018 2017 2016)
  Non-year tokens (e.g., LAST_5_YEARS) are kept at the end in their original order
- Flags anything else as wrong_order
- Writes a CSV summary to: output{SUFIX}.csv

Notes
-----
- Input is produced manually (e.g. via):
  https://server.com/dhis2/api/visualizations?fields=rows[*],lastUpdated,created,lastUpdatedBy,id,name&paging=false
- Keep one file per instance by changing SUFFIX (e.g., "_dev", "_prod") and naming your input:
  visualizations_check_dev.json, visualizations_check_prod.json, etc.
"""

import csv, json, os, re, sys

SUFIX = "_prod"
YEAR = re.compile(r"^\d{4}$")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, f"visualizations_check{SUFIX}.json")
OUTPUT_FILE = os.path.join(BASE_DIR, f"output{SUFIX}.csv")

def load_visualizations(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and isinstance(data.get("visualizations"), list):
        return data["visualizations"]
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError("Unsupported JSON structure")

def get_pe_ids(v):
    rows = v.get("rows", [])
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and row.get("dimension") == "pe":
            items = row.get("items", [])
            return [str(it["id"]) for it in items if isinstance(it, dict) and "id" in it]
    return None

def sort_years(ids, reverse=False):
    nums = [x for x in ids if YEAR.match(x)]
    rest = [x for x in ids if not YEAR.match(x)]
    nums_sorted = sorted(nums, key=lambda x: int(x), reverse=reverse)
    return nums_sorted + rest

def analyze(v):
    ids = get_pe_ids(v)
    if ids is None:
        return ("no_pe_dimension", [], [])
    asc = sort_years(ids, reverse=False)
    desc = sort_years(ids, reverse=True)
    if ids == asc:
        return ("ok", ids, asc)
    if ids == desc:
        return ("ok_desc", ids, asc)  # keep asc as the reference/expected
    return ("wrong_order", ids, asc)

def main():
    try:
        print(f"Loading: {INPUT_FILE}")
        visualizations = load_visualizations(INPUT_FILE)
    except Exception as e:
        print(f"Error loading JSON: {e}", file=sys.stderr)
        sys.exit(1)

    results = []
    total = len(visualizations)
    wrong = 0
    no_pe = 0

    for v in visualizations:
        vid = v.get("id", "")
        name = v.get("name", "")
        created = v.get("created", "")
        last_updated = v.get("lastUpdated", "")

        status, current, expected_asc = analyze(v)
        if status == "wrong_order":
            wrong += 1
            print(f"[WRONG ORDER] {name} ({vid}) | current={current} | expected(asc)={expected_asc}")
        elif status == "no_pe_dimension":
            no_pe += 1

        results.append({
            "id": vid,
            "created": created,
            "lastUpdated": last_updated,
            "name": name,
            "status": status,
            "current_order": " ".join(current),
            "expected_order": " ".join(expected_asc),
        })

    print("\nSummary")
    print(f"  Total               : {total}")
    print(f"  Without 'pe'        : {no_pe}")
    print(f"  Wrong order         : {wrong}")
    print(f"  Valid (with 'pe')   : {total - wrong - no_pe}")

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "created", "lastUpdated", "name", "status", "current_order", "expected_order"]
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"\nCSV written: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
