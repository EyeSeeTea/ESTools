import json
import sys
import time
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import argparse
import os

class DHIS2Monitor:
    def __init__(self, config):
        self.server = config.get('server')
        self.auth = HTTPBasicAuth(config.get('user'), config.get('password'))
        self.interval = 30  # Interval of 30 seconds between comparisons

        folder = config.get('folder')
        self.last_values = os.path.join(folder, "last_values.json")
        self.usergroups_file = os.path.join(folder, "usergroups.json")
        self.control_file = os.path.join(folder, "control_file.json")

    def request(self, url):
        response = requests.get(url, auth=self.auth)
        return response

    def clean_cache(self):
        return self.request(f'{self.server}api/38/maintenance?cacheClear=true')

    def get_users_and_groups(self):
        """Fetches the list of users and their user group sizes."""
        return self.request(f'{self.server}api/users?fields=id,userGroups::size&paging=false')

    def user_groups_updated_recently(self):
        """Checks if any user groups were updated in the last 5 minutes and in that case exit."""
        five_minutes_ago = (datetime.now() - timedelta(minutes=5)
                            ).strftime("%Y-%m-%dT%H:%M:%S")
        response = self.request(
            f'{self.server}api/userGroups?filter=lastUpdated:gt:{five_minutes_ago}&paging=false')

        if response.status_code == 200:
            usergroups = response.json().get('userGroups', [])
            return len(usergroups) > 0
        else:
            print(f"Error checking userGroups: {response.status_code} - {response.text}")
            sys.exit(0)

    def filter_common_users(self, current_users, previous_users):
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

    def save_state(self, filename, data):
        """Saves the given data to the specified file."""
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

    def load_state(self, filename):
        """Loads and returns data from the specified file."""
        try:
            with open(filename, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def states_are_different(self, state1, state2):
        """Compares two states after filtering common users excluding new or deleted users."""
        state1, state2 = self.filter_common_users(state1, state2)
        return state1 != state2

    def get_date(self):
        return datetime.now().strftime("%d_%m_%Y_%H_%M")

    def handle_api_error(self):
        print("API request failed")
        sys.exit(0)

    def save_control_file(self, date):
        """Saves the date in control file when a cache issue has been identified to be handled by monit."""
        control_data = {"last_cache_issue_date": date}
        with open(self.control_file, 'w') as file:
            json.dump(control_data, file, indent=4)
        print(f"Saved cache issue date to {self.control_file}")

    def compare_states_and_save(self, data_before_clean_cache, data_after_cache_clean):
        """Handles the comparison of states and decides when to save."""
        if self.states_are_different(data_before_clean_cache, data_after_cache_clean):
            print("Clean cache fixed the problem. Saving the new state and updating control file.")
            self.save_usergroups_to_analyze(self.get_date())
            self.save_state(self.last_values, data_after_cache_clean)
            self.save_control_file(self.get_date())
        else:
            print("No cache issue detected. Legitimate changes detected. Saving new state.")
            self.save_state(self.last_values, data_after_cache_clean)

    def save_usergroups_to_analyze(self, date):
        """Saves the user groups for analysis."""
        response = self.request(f'{self.server}api/userGroups?fields=*&paging=false')
        if response.status_code == 200:
            usergroups_data = sorted(response.json().get(
                'userGroups', []), key=lambda x: x['id'])
            self.save_state(f"{date}_{self.usergroups_file}", usergroups_data)
        return response

    def create_last_changed_file_if_not_exists(self):
        """Creates last_changed.json if it doesn't exist with the current server data."""
        if not self.load_state(self.last_values):  # Check if file is empty or doesn't exist
            print(f"{self.last_values} not found, creating it with the current state.")
            response = self.get_users_and_groups()
            if response.status_code == 200:
                current_data = sorted(
                    response.json()["users"], key=lambda x: x['id'])
                self.save_state(self.last_values, current_data)
                print(f"Saved current state from the server to {self.last_values}.")
            else:
                print(f"Failed to fetch data from server to create {self.last_values}.")
                sys.exit(0)


def main(config_path):
    print("Starting at:" + datetime.now().strftime("%d_%m_%Y_%H_%M"))

    with open(config_path, 'r') as conf_file:
        config_data = json.load(conf_file)

    monitor = DHIS2Monitor(config_data)

    # This is used in the first execution.
    monitor.create_last_changed_file_if_not_exists()

    # Check if any user groups were updated recently and exit if true
    if monitor.user_groups_updated_recently():
        print("User groups updated recently. Exiting.")
        sys.exit(0)

    last_changed_data = monitor.load_state(monitor.last_values)
    response = monitor.get_users_and_groups()

    if response.status_code != 200:
        monitor.handle_api_error()

    current_data = sorted(response.json()["users"], key=lambda x: x['id'])
    print("Comparing current state.")

    if monitor.states_are_different(last_changed_data, current_data):
        print("Changes detected. Cleaning cache and waiting.")
        monitor.clean_cache()
        time.sleep(monitor.interval)

        new_response = monitor.get_users_and_groups()
        if new_response.status_code != 200:
            monitor.handle_api_error()

        current_data_after_cache_clean = sorted(
            new_response.json()["users"], key=lambda x: x['id'])

        monitor.compare_states_and_save(current_data, current_data_after_cache_clean)
    else:
        print("No changes detected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DHIS2 User-Usergroup notification script")
    parser.add_argument('--config', required=True, help="Config file path")
    args = parser.parse_args()
    main(args.config)