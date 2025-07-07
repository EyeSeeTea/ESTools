# DHIS2 Organisation Units Comparison

This project allows you to **download and compare organisation units (orgUnits)** across multiple DHIS2 instances (e.g. DEV, INDIV, PROD) using authenticated API access.

## Step 1: Download OrgUnits from Each Instance

Run the script:
python download_all_orgunits.py
Before executing, **hardcode the following variables** in the script to match each instance:

```python
BASE_URL = "https://play/dhis2"
OUTPUT_FILE = "organisation_units.json"
USERNAME = ""
PASSWORD = ""
```

Repeat this step for each instance (DEV, INDIV, PROD, etc.), saving the result to a different JSON file each time:

organisation_units_dev.json

organisation_units_indiv.json

organisation_units_prod.json

You can also modify the fields being collected from the DHIS2 API in the script if needed.

Step 2: Merge JSON Files into a Local SQLite Database
Edit the file merge_all_jsons_in_a_single_db.py to define which JSON files to load and what table name each will have:

```json
json_files = {
    "organisation_units_dev.json": "orgunits_dev",
    "organisation_units_indiv.json": "orgunits_indiv",
    "organisation_units_prod.json": "orgunits_prod",
}
```

Then run:

```bash
  python merge_all_jsons_in_a_single_db.py
```

This will create a local SQLite database with one table per orgUnit file.

Step 3: Create Views for Comparing OrgUnits Across Instances
Use the following SQL statements to create views that help identify discrepancies between the datasets:

```sql
CREATE VIEW exists_in_dev_but_not_in_indiv AS
SELECT *
FROM orgunits_dev i
WHERE NOT EXISTS (
    SELECT 1
    FROM orgunits_indiv p
    WHERE p.id = i.id
);

CREATE VIEW exists_in_indiv_but_not_in_prod AS
SELECT *
FROM orgunits_indiv i
WHERE NOT EXISTS (
    SELECT 1
    FROM orgunits_prod p
    WHERE p.id = i.id
);

CREATE VIEW exists_in_prod_but_not_in_indiv AS
SELECT *
FROM orgunits_prod i
WHERE NOT EXISTS (
    SELECT 1
    FROM orgunits_indiv p
    WHERE p.id = i.id
);
```

These views allow you to detect missing or extra orgUnits between pairs of instances.

Optional Adjustments
You may adjust the fields collected from the DHIS2 API in download_all_orgunits.py.

You can also change the table structure or filtering logic in merge_all_jsons_in_a_single_db.py as needed for your comparison.
