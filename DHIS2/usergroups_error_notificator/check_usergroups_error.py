import json
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import argparse

changes_detected = False
server = ""
auth = ""
all_users_request = "api/users.json?fields=id&paging=false"


def get_user_groups(user_id):
    global auth
    global server
    url = f'{server}api/users/{user_id}.json?fields=userGroups'
    response = requests.get(url, auth=auth)
    return response


def get_usergroups_filtered(user_id):
    global auth
    global server
    url_usergroups = f'{server}api/userGroups.json?fields=id&filter=users.id:eq:{user_id}&paging=false'
    response_usergroups = requests.get(url_usergroups, auth=auth)
    return response_usergroups


def order(item):
    if 'userGroups' in item:
        item['userGroups'] = sorted(item['userGroups'], key=lambda x: x['id'])
    return item


def order_json(value):
    value = order(value)
    return value


def getTime():
    now = datetime.now()
    formatted_date_time = now.strftime("%d_%m_%Y_%H_%M")
    return formatted_date_time


def main(config_path):
    global auth
    global server
    global changes_detected

    print("Starting at:" + getTime())
    with open(config_path, 'r') as conf_file:
        config_data = json.load(conf_file)
    server = config_data.get('server')
    mode = config_data.get("mode")
    username = config_data.get('user')
    password = config_data.get('password')
    auth = HTTPBasicAuth(username, password)
    if mode == "ALL":
        user_ids = requests.get(server+all_users_request, auth=auth).json()
    else:
        user_ids = config_data.get("user_ids")
    control_file = config_data.get("control_file")
    log_file = config_data.get("log_file")

    for user_id in user_ids["users"]:
        if check_user_changes(user_id["id"], control_file, log_file):
            changes_detected = True

    print(getTime())
    if changes_detected:
        print("USERGROUP ERROR DETECTED")
    else:
        print("NO ERROR DETECTED")


def check_user_changes(user_id, control_users_file, log_file):
    response = get_user_groups(user_id)
    response_usergroups = get_usergroups_filtered(user_id)

    if response.status_code == 200 and response_usergroups.status_code == 200:
        value = order_json(response.json())
        usergroupsvalue = order_json(response_usergroups.json())

        if value != usergroupsvalue:
            formatted_date_time = getTime()
            print(value)
            print(usergroupsvalue)
            print(formatted_date_time)
            print(f"User {user_id} changed")
            print("------------------------")

            with open(control_users_file, 'w') as f:
                f.write(formatted_date_time)

            with open(log_file, 'a') as f:
                f.write(formatted_date_time)
                f.write("User usergroups")
                f.write(value)
                f.write("Usergroups filtered by user")
                f.write(usergroupsvalue)
                f.write("-----")
            return True
        else:
            print(user_id + " OK")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DHIS2 USER-USERGROUP notification")
    parser.add_argument('--config', required=True, help="Config file path")
    args = parser.parse_args()
    main(args.config)
