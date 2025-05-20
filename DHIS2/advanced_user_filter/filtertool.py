import json
import csv
import os
from datetime import datetime

# === CONFIGURATION LOADED FROM JSON ===

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

def get_field(config, key, default):
    value = config.get(key)
    if value in (None, "", [], {}):
        return default
    return value

def get_mandatory_field(config, key):
    value = config.get(key)
    if value in (None, "", [], {}):
        raise ValueError(f"Missing or empty mandatory configuration key: '{key}'")
    return value



INPUT_DIR = get_field(config, "INPUT_DIR", "INPUT_DIR")
OUTPUT_DIR = get_field(config, "OUTPUT_DIR", "OUTPUT_DIR")
DEPARTMENTS = get_mandatory_field(config, "DEPARTMENTS")
SELECTED_FIELDS = get_mandatory_field(config, "SELECTED_FIELDS")
FIELD_NAME_TRANSLATIONS = get_field(config, "FIELD_NAME_TRANSLATIONS", {})

# Filtros opcionales
ADDITIONAL_FILTERS = get_field(config, "ADDITIONAL_FILTERS", {})
REQUIRED_GROUPS = get_field(config, "REQUIRED_GROUPS", [])
EXCLUDED_GROUPS = get_field(config, "EXCLUDED_GROUPS", [])
EXCLUDED_USERNAMES = get_field(config, "EXCLUDED_USERNAMES", [])
FILTER_DISABLED_USERS = get_field(config, "FILTER_DISABLED_USERS", False)
DISABLED_USER_EXCEPTIONS = get_field(config, "DISABLED_USER_EXCEPTIONS", [])
COMPUTED_FIELDS = get_field(config, "COMPUTED_FIELDS", [])

def load_users(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f).get("users", [])

def user_in_groups(user, target_groups):
    return any(group.get("name") in target_groups for group in user.get("userGroups", []))

def has_group_prefix(user, prefixes):
    for group in user.get("userGroups", []):
        if any(group.get("name", "").startswith(prefix) for prefix in prefixes):
            return True
    return False

def is_disabled(user):
    if not user.get("disabled", False):
        return False
    if DISABLED_USER_EXCEPTIONS and user_in_groups(user, DISABLED_USER_EXCEPTIONS):
        return False
    return True

def is_excluded_user(user):
    return user.get("username") in EXCLUDED_USERNAMES

def user_passes(user):
    if EXCLUDED_USERNAMES and is_excluded_user(user):
        return False
    if FILTER_DISABLED_USERS and is_disabled(user):
        return False
    for key, expected_value in ADDITIONAL_FILTERS.items():
        if user.get(key) != expected_value:
            return False
    if REQUIRED_GROUPS and not user_in_groups(user, REQUIRED_GROUPS):
        return False
    if EXCLUDED_GROUPS and user_in_groups(user, EXCLUDED_GROUPS):
        return False
    return True

def format_value(value):
    if isinstance(value, list):
        if all(isinstance(v, dict) and list(v.keys()) == ["name"] for v in value):
            return "|".join(v["name"] for v in value)
        if all(isinstance(v, dict) and "id" in v and "name" in v for v in value):
            return "|".join(f"{v['id']}:{v['name']}" for v in value)
        return json.dumps(value, ensure_ascii=False)
    return str(value)

def get_nested_value(obj, key_path):
    if "." in key_path:
        first, second = key_path.split(".", 1)
        inner = obj.get(first)
        if isinstance(inner, dict):
            value = inner.get(second)
            return value if value not in (None, "-") else "-"
        return "-"
    else:
        value = obj.get(key_path)
        return value if value not in (None, "-") else "-"

def build_user_row(user, fields):
    row = {}
    for field in fields:
        row[field] = format_value(get_nested_value(user, field))
    computed = compute_additional_fields(user)
    for field in COMPUTED_FIELDS:
        row[field] = computed.get(field, "")
    return row

def filter_users(users, department):
    return [
        user for user in users
        if has_group_prefix(user, department["prefixes"]) and user_passes(user)
    ]

def months_since(date_str):
    try:
        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
        now = datetime.now()
        delta = (now.year - date.year) * 12 + (now.month - date.month)
        return str(max(delta, 0))
    except Exception:
        return ""

def compute_additional_fields(user):
    values = {}
    password_date = (
        user.get("userCredentials", {}).get("passwordLastUpdated")
        or user.get("created")
    )
    values["monthsSincePasswordUpdate"] = months_since(password_date)
    return values

def write_csv(users, department_name, source_file, fields):
    if not users:
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base = os.path.splitext(os.path.basename(source_file))[0]
    output_file = f"{base}_{department_name}_filtered_users.csv"
    output_path = os.path.join(OUTPUT_DIR, output_file)

    with open(output_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        translated_headers = [FIELD_NAME_TRANSLATIONS.get(f, f) for f in fields]
        writer.writerow(dict(zip(fields, translated_headers)))
        for user in users:
            writer.writerow(build_user_row(user, fields))

    print(f"Saved: {output_path}")

def process_files():
    for file in os.listdir(INPUT_DIR):
        if not file.endswith(".json"):
            continue
        path = os.path.join(INPUT_DIR, file)
        users = load_users(path)
        for department in DEPARTMENTS:
            dept_users = filter_users(users, department)
            write_csv(dept_users, department["name"], file, SELECTED_FIELDS)

def main():
    process_files()

if __name__ == "__main__":
    main()
