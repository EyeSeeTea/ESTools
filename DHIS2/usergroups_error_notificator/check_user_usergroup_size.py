import json
import sys
import time
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import argparse

# Globals
server = ""
auth = ""
interval = 30  # Interval of 30 seconds between comparisons
last_values = "last_values.json"
usergroups_file = "usergroups.json"
control_file = "control_file.json"


def request(url):
    response = requests.get(url, auth=auth)
    return response


def clean_cache():
    return request(f'{server}api/38/maintenance?cacheClear=true')


def get_users_and_groups():
    """Fetches the list of users and their user group sizes."""
    return request(f'{server}api/users?fields=id,userGroups::size&paging=false')


def user_groups_updated_recently():
    """Checks if any user groups were updated in the last 5 minutes and in that case exit."""
    five_minutes_ago = (datetime.now() - timedelta(minutes=5)
                        ).strftime("%Y-%m-%dT%H:%M:%S")
    response = request(
        f'{server}api/userGroups?filter=lastUpdated:gt:{five_minutes_ago}&paging=false')

    if response.status_code == 200:
        usergroups = response.json().get('userGroups', [])
        return len(usergroups) > 0
    else:
        print(
            f"Error checking userGroups: {response.status_code} - {response.text}")
        sys.exit(0)


def filter_common_users(current_users, previous_users):
    """Filters out added or deleted users to compare only common ones to avoid false positives."""
    current_users_dict = {user['id']: user for user in current_users}
    previous_users_dict = {user['id']: user for user in previous_users}

    common_user_ids = set(current_users_dict.keys()).intersection(
        set(previous_users_dict.keys()))
    filtered_current_users = [current_users_dict[user_id]
                              for user_id in common_user_ids]
    filtered_previous_users = [previous_users_dict[user_id]
                               for user_id in common_user_ids]

    return filtered_current_users, filtered_previous_users


def save_state(filename, data):
    """Saves the given data to the specified file."""
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def load_state(filename):
    """Loads and returns data from the specified file."""
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def states_are_different(state1, state2):
    """Compares two states after filtering common users excluding new or deleted users."""
    state1, state2 = filter_common_users(state1, state2)
    return state1 != state2


def get_date():
    return datetime.now().strftime("%d_%m_%Y_%H_%M")


def handle_api_error():
    print("API request failed")
    sys.exit(0)


def save_control_file(date):
    """Saves the date in control file when a cache issue has been identified to be handled by monit."""
    control_data = {"last_cache_issue_date": date}
    with open(control_file, 'w') as file:
        json.dump(control_data, file, indent=4)
    print(f"Saved cache issue date to {control_file}")


def compare_states_and_save(data_before_clean_cache, data_after_cache_clean):
    """Handles the comparison of states and decides when to save."""
    if states_are_different(data_before_clean_cache, data_after_cache_clean):
        print(
            "Clean cache fixed the problem. Saving the new state amd update control file.")
        save_usergroups_to_analyze(get_date())
        save_state(last_values, data_after_cache_clean)
        save_control_file(get_date())
    else:
        print("No cache issue detected. Legitimate changes detected. Saving new state.")
        save_state(last_values, data_after_cache_clean)


def save_usergroups_to_analyze(date):
    """Saves the user groups for analysis."""
    response = request(f'{server}api/userGroups?fields=*&paging=false')
    if response.status_code == 200:
        usergroups_data = sorted(response.json().get(
            'userGroups', []), key=lambda x: x['id'])
        save_state(date + usergroups_file, usergroups_data)
    return response


def create_last_changed_file_if_not_exists():
    """Creates last_changed.json if it doesn't exist with the current server data."""
    if not load_state(last_values):  # Check if file is empty or doesn't exist
        print(f"{last_values} not found, creating it with the current state.")
        response = get_users_and_groups()
        if response.status_code == 200:
            current_data = sorted(
                response.json()["users"], key=lambda x: x['id'])
            save_state(last_values, current_data)
            print(f"Saved current state from the server to {last_values}.")
        else:
            print(f"Failed to fetch data from server to create {last_values}.")
            sys.exit(0)


def main(config_path):
    global auth
    global server

    print("Starting at:" + get_date())

    with open(config_path, 'r') as conf_file:
        config_data = json.load(conf_file)
    server = config_data.get('server')
    auth = HTTPBasicAuth(config_data.get('user'), config_data.get('password'))
    # This is used in the first execution.
    create_last_changed_file_if_not_exists()
    # Check if any user groups were updated recently and exit if true
    if user_groups_updated_recently():
        print("User groups updated recently. Exiting.")
        sys.exit(0)

    last_changed_data = load_state(last_values)
    response = get_users_and_groups()

    if response.status_code != 200:
        handle_api_error()

    current_data = sorted(response.json()["users"], key=lambda x: x['id'])
    print("Comparing current state.")

    if states_are_different(last_changed_data, current_data):
        print("Changes detected. Cleaning cache and waiting.")
        clean_cache()
        time.sleep(interval)

        new_response = get_users_and_groups()
        if new_response.status_code != 200:
            handle_api_error()

        current_data_after_cache_clean = sorted(
            new_response.json()["users"], key=lambda x: x['id'])

        compare_states_and_save(current_data, current_data_after_cache_clean)
    else:
        print("No changes detected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DHIS2 User-Usergroup notification script")
    parser.add_argument('--config', required=True, help="Config file path")
    args = parser.parse_args()
    main(args.config)
