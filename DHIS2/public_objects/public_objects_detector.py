#!/usr/bin/env python3
import argparse
import json
import time
from datetime import datetime
import requests

proxies={}

# Retry wrapper for resilient API calls
def with_retries(func, retries, delay):
    last_exception = None

    for attempt in range(1, retries + 1):
        try:
            result = func()
            return result
        except Exception as e:
            last_exception = e
            print(f"[{attempt}/{retries}] Error: {e}")
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)

    # Final failure after all retries
    raise last_exception

# Load JSON configuration from file
def load_config(path):
    with open(path) as f:
        return json.load(f)

# Fetch data from a DHIS2 SQL View using token auth
def fetch_sql_data(url, view_id, token):
    headers = {"Authorization": f"ApiToken {token}"}
    full_url = f"{url}/api/sqlViews/{view_id}/data"
    response = requests.get(full_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    return response.json()

# Get public objects breakdown from SQL View
def get_public_objects(url, view_id, token):
    data = fetch_sql_data(url, view_id, token)
    return data["listGrid"]["rows"]

# Get total public objects count from SQL View
def get_total_count(url, view_id, token):
    data = fetch_sql_data(url, view_id, token)
    return data["pager"]["total"]

# Send a dataValue payload to DHIS2 using token auth
def send_data_value(output_url, payload, token):
    headers = {
        "Authorization": f"ApiToken {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    url = f"{output_url}/api/dataValues"
    response = requests.post(url, data=payload, headers=headers, proxies=proxies)
    response.raise_for_status()
    return response

# Send metric with retries and logging
def send_metric(name, payload, config):
    def send():
        return send_data_value(config["output_server"], payload, config["token"])
    print(f"Sending {name}...")
    response = with_retries(send, config["max_retries"], config["retry_interval_seconds"])
    if response.status_code in (200, 201):
        print(f"✅ {name} sent successfully")
    else:
        print(f"⚠️ {name} failed with status: {response.status_code}")

def main():
    global proxies
    print(f"== START {datetime.now().isoformat()} ==")

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="Path to config.json")
    args = parser.parse_args()
    config = load_config(args.config_file)
    proxies = config.get("proxy", {})
    period = datetime.now().strftime("%Y%m%d")

    for server in config["servers"]:
        url = server["url"]
        co = server["co"]
        token = server["token"]

        print(f"\n-- Processing {url}")

        def retrieve_objects():
            return get_public_objects(url, config["sql_views"]["public_objects"], token)

        def retrieve_total():
            return get_total_count(url, config["sql_views"]["total"], token)

        try:
            public_objects = with_retries(retrieve_objects, config["max_retries"], config["retry_interval_seconds"])
            # Transform [['key1', 'value1'], ['key2', 'value2']] into [{'key1': 'value1'}, {'key2': 'value2'}]
            public_objects = [{k: v} for k, v in public_objects]

            total_count = with_retries(retrieve_total, config["max_retries"], config["retry_interval_seconds"])
            base_payload = {
                "co": co,
                "ds": config["dataset_id"],
                "ou": config["org_unit_id"],
                "pe": period
            }

            total_payload = {
                **base_payload,
                "de": config["data_element_ids"]["total"],
                "value": total_count
            }

            objects_payload = {
                **base_payload,
                "de": config["data_element_ids"]["public_objects"],
                "value": json.dumps(public_objects)
            }

            send_metric(f"Total count in {url}", total_payload, config)
            send_metric("Public objects breakdown", objects_payload, config)

        except Exception as e:
            print(f"❌ Skipping server {url} due to unrecoverable error: {e}")

    print(f"== END {datetime.now().isoformat()} ==")

if __name__ == "__main__":
    main()
