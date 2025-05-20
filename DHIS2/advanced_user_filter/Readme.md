# DHIS2 User Filtering and Export Tool

This repository contains a Python tool for processing DHIS2-style user export JSON files. The tool filters users based on configurable rules and generates one CSV file per department. An optional script is also provided to consolidate all CSVs into a single Excel file.

---

## 📁 Project Structure

- `filtertool.py`: Main script that parses JSON user dumps and applies filters defined in `config.json`.
- `create_excel.py`: Combines all filtered CSVs from the output folder into a single `.xlsx` file, with one sheet per CSV.
- `config.json`: Centralized configuration file for filtering, grouping, and output behavior.
- `test_months_since.py`: Unit tests for the `months_since` function and related field computation logic.

---
## Configuration

All behavior is defined in `config.json`.

### Input and Output

- `INPUT_DIR`: Directory containing the DHIS2 JSON user exports. (example users_prod.json users_preprod.json...)
- `OUTPUT_DIR`: Destination directory for the generated CSV files.

### Department Assignment

Users are assigned to departments based on prefixes matched against their user group names.

Example:

```
DEPARTMENTS = [
    {"name": "DEP1", "prefixes": ["PREX1-", "ALTPREX1"]},
    {"name": "DEP2, "prefixes": ["PREX2"]},
    ...
]
```
### Filtering Rules
ADDITIONAL_FILTERS: Dictionary of field-value pairs. Users must match all to be included.

REQUIRED_GROUPS: If set, users must belong to at least one of the listed user groups.

EXCLUDED_GROUPS: If set, users belonging to any of these groups are excluded.

EXCLUDED_USERNAMES: List of usernames to exclude explicitly.

FILTER_DISABLED_USERS: If True, disables users unless they belong to an exception group.

DISABLED_USER_EXCEPTIONS: List of group names that override the disabled flag.

### Output Structure
SELECTED_FIELDS: Fields to include in the CSV output. Supports nested access (e.g., userCredentials.passwordLastUpdated).

COMPUTED_FIELDS: List of dynamically generated fields. Currently includes:

monthsSincePasswordUpdate: Number of months since the user's password was last updated.

FIELD_NAME_TRANSLATIONS: Optional mapping to replace internal field names with user-friendly column headers.

### Running the Script
From the project directory:

`python filtertool.py`
This will process all .json files in input/ and create filtered .csv files in output/, grouped by department.

To generate a single Excel file with each CSV as a separate tab:

`python create_excel.py`
This will generate a file ready to be imported in google spreadsheet or similar, such as:

`output/combined_output_2025-05-20_14-30.xlsx`
The timestamp ensures that files are not overwritten between runs.

Notes
Nested fields are safely extracted. If a value is missing or empty, "-" is written to the CSV.

Group checks are based on the "name" attribute of each entry in userGroups.

The script assumes input JSON follows DHIS2's user export format ({"users": [...]}).

The Excel generator trims sheet names to a maximum of 31 characters (Excel limitation).

# # Testing
A small test suite exists for date-based logic:

pytest test_months_since.py
Verifies the correctness of months_since() and compute_additional_fields().

Uses freezegun to freeze time for predictable results.