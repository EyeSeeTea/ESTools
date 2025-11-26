# DHIS2 Python Skeleton

Small set of DHIS2 utilities (“use cases”):
- Generate SQL for missing attribute values (`create-missing-values`).
- Update data element UIDs and codes inside a blueprint XLSX (`update-blueprint-dataelements`).

## Installation (recommended: virtualenv)
```bash
python3 -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows

pip install openpyxl
pip install requests
```

## Quick start
Run commands from the project root.

### Update data element UIDs in a blueprint
Reads an XLSX from `input/` and writes the result to `output/` (adds a timestamp if the file already exists).
```bash
python3 main_skeleton.py \
  --use-case update-blueprint-dataelements \
  --base-url https://server \
  --jsessionid token \
  --xlsx-file Blueprint_HFW.xlsx \
  --output-xlsx-file blueprint_apvd.xlsx
```
Key parameters:
- `--sheets`: sheet names to process (default `Module 1 - APVD` and `Module 2 - APVD`).
- `--name-col`: column with the data element name (index, letter, or header; default `3`).
- `--uid-col`: column to write the UID (default `UID`; accepts index, letter, or header).
- `--code-col`: column to write the code (default `Code`; accepts index, letter, or header).
- `--data-start-row`: start row when no headers are present (default `2`; auto-adjusts if headers are detected).

What it does:
- Ensures names end with `-APVD`.
- Searches DHIS2 with `name:like`; if one exact match is found, writes UID (and code when present).
- If no exact match, shows candidates and prompts for UID manually in the console.

### Reorder sections alphabetically
Reads a JSON of sections from `input/` (either a list, or an object with a `sections` array) and rewrites `sortOrder` starting at 1 based on alphabetical name order.
```bash
python3 main_skeleton.py \
  --use-case reorder-sections \
  --sections-file sections_order.json \
  --sections-output-file sections_order_sorted.json
```
Tip: The sample data was fetched via `https://server/api/sections?filter=dataSet.id:in:[NnhyjiUbcJN]&fields=*&paging=false`.

### Create SQL for missing attributes
Generates INSERT statements for missing tracked-entity attributes (reads CSV from `input/`, writes SQL to `output/`):
```bash
python3 main_skeleton.py \
  --use-case create-missing-values \
  --base-url https://server \
  --jsessionid token \
  --input-file teis_without_storedby.csv \
  --output-file insert_attr_fullname.sql
```

## Notes
- Credentials can also come from `.env` (`BASE_URL` and `JSESSIONID`); the script will ask for confirmation before using them.
- For more options, run `python3 main_skeleton.py --help`.
