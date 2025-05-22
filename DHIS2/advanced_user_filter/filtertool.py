import argparse
import json
import csv
import os
import operator
from datetime import datetime

# === CONFIGURATION LOADED FROM JSON ===

CONFIG_DEFAULT = "config.json"
NOT_EMPTY = '__NOT_EMPTY__'
MISSING = '__MISSING__'
PRESENT = '__PRESENT__'

ops = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le
}

def parse_args():
    parser = argparse.ArgumentParser(description="Process an input json file to extract several CSV files based on a configuration file. Optionally set a specific config file instead of the default")
    parser.add_argument(
        "--config",
        type=str,
        default=CONFIG_DEFAULT,
        help=f"Path to the config file (by default {CONFIG_DEFAULT})"
    )
    return parser.parse_args()

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

def load_config(config_file):
    global INPUT_DIR, OUTPUT_DIR, DEPARTMENTS, SELECTED_FIELDS, FIELD_NAME_TRANSLATIONS
    global ADDITIONAL_FILTERS, REQUIRED_GROUPS, EXCLUDED_GROUPS, EXCLUDED_USERNAMES, FILTER_DISABLED_USERS, DISABLED_USER_EXCEPTIONS, COMPUTED_FIELDS, REQUIRED_ALL_GROUPS, COMPUTED_FILTERS
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"Error: Missing config file '{config_file}'")

    with open(config_file, encoding="utf-8") as f:
        config = json.load(f)

    INPUT_DIR = get_field(config, "INPUT_DIR", "INPUT_DIR")
    OUTPUT_DIR = get_field(config, "OUTPUT_DIR", "OUTPUT_DIR")
    DEPARTMENTS = get_mandatory_field(config, "DEPARTMENTS")
    SELECTED_FIELDS = get_mandatory_field(config, "SELECTED_FIELDS")
    FIELD_NAME_TRANSLATIONS = get_field(config, "FIELD_NAME_TRANSLATIONS", {})
    
    # Not required filters
    ADDITIONAL_FILTERS = get_field(config, "ADDITIONAL_FILTERS", {})
    REQUIRED_GROUPS = get_field(config, "REQUIRED_GROUPS", [])
    REQUIRED_ALL_GROUPS = get_field(config, "REQUIRED_ALL_GROUPS", [])
    EXCLUDED_GROUPS = get_field(config, "EXCLUDED_GROUPS", [])
    EXCLUDED_USERNAMES = get_field(config, "EXCLUDED_USERNAMES", [])
    FILTER_DISABLED_USERS = get_field(config, "FILTER_DISABLED_USERS", False)
    DISABLED_USER_EXCEPTIONS = get_field(config, "DISABLED_USER_EXCEPTIONS", [])
    COMPUTED_FIELDS = get_field(config, "COMPUTED_FIELDS", [])
    COMPUTED_FILTERS = get_field(config, "COMPUTED_FILTERS", [])

def load_users(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f).get("users", [])

def user_in_groups(user, target_groups):
    return any(group.get("name") in target_groups for group in user.get("userGroups", []))

def user_in_all_groups(user, target_groups):
    user_group_names = {group.get("name") for group in user.get("userGroups", [])}
    return all(target in user_group_names for target in target_groups)

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
        if expected_value == NOT_EMPTY:
            if not user.get(key):  # False for None, '', [], {}, 0, false
                return False
        elif expected_value == MISSING:
            if key in user:
                return False
        elif expected_value == PRESENT:
            if key not in user:
                return False
        else:
            if user.get(key) != expected_value:
                return False
    if REQUIRED_GROUPS and not user_in_groups(user, REQUIRED_GROUPS):
        return False
    if REQUIRED_ALL_GROUPS and not user_in_all_groups(user, REQUIRED_ALL_GROUPS):
        return False
    if EXCLUDED_GROUPS and user_in_groups(user, EXCLUDED_GROUPS):
        return False
    if COMPUTED_FILTERS:
        computed = compute_additional_fields(user)
        for computed_filter in COMPUTED_FILTERS:
            for key, expected_expression in computed_filter.items():
                ckey = computed.get(key, "")
                op = ops.get(expected_expression["op"])
                expected_value = expected_expression["value"]
                x = op(ckey, expected_value)
                if op is None:
                    raise ValueError(f"Operator not supported {expected_expression['op']}")
                # try to convert to numbers before comparisson, but will still compare strings if not
                try:
                    ckey = float(ckey)
                    expected_value = float(expected_value)
                except (ValueError, TypeError):
                    pass 

                if not op(ckey, expected_value):
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
        user.get("passwordLastUpdated")
        or user.get("userCredentials", {}).get("passwordLastUpdated")
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
        users_in_dept = set()
        for department in DEPARTMENTS:
            dept_users = filter_users(users, department)
            write_csv(dept_users, department["name"], file, SELECTED_FIELDS)
            for user in dept_users:
                users_in_dept.add(user.get("id"))
        other_users = [user for user in users if user.get("id") not in users_in_dept and user_passes(user)]
        write_csv(other_users, "OTHER", file, SELECTED_FIELDS)

def main():
    args = parse_args()
    load_config(args.config)
    process_files()

if __name__ == "__main__":
    main()
