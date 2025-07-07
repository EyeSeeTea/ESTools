import sqlite3
import json
import os

# Files and tables
json_files = {
    "organisation_units_dev.json": "orgunits_dev",
    "organisation_units_indiv.json": "orgunits_indiv",
    "organisation_units_prod.json": "orgunits_prod",
}

conn = sqlite3.connect("orgunits_comparison.db")
cur = conn.cursor()

for file, table in json_files.items():
    if not os.path.exists(file):
        print(f"File not found: {file}")
        continue

    print(f"Processing {file} → {table}")

    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f).get("organisationUnits", [])

    #Create tables by expected fields
    cur.execute(f"DROP TABLE IF EXISTS {table}")
    cur.execute(f"""
        CREATE TABLE {table} (
            id TEXT PRIMARY KEY,
            code TEXT,
            name TEXT,
            shortName TEXT,
            created TEXT,
            path TEXT,
            level INTEGER,
            geometry_type TEXT,
            children INTEGER
        )
    """)

    # Insert data
    for ou in data:
        cur.execute(f"""
            INSERT OR REPLACE INTO {table} (id, code, name, shortName, created, path, level, geometry_type, children)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ou.get("id"),
            ou.get("code"),
            ou.get("name"),
            ou.get("shortName"),
            ou.get("created"),
            ou.get("path"),
            ou.get("level"),
            ou.get("geometry", {}).get("type") if ou.get("geometry") else None,
            ou.get("children")
        ))

conn.commit()
conn.close()
