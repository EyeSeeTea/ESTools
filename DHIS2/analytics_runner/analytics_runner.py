import time
import requests
import argparse

MAX_WAIT_TIME = 1800  # 30 minutes in seconds
CHECK_INTERVAL = 30  # 30 seconds

MAINTENANCE_ENDPOINT = "/api/41/maintenance?analyticsTableClear=true"
RESOURCE_TABLES_ENDPOINT = "/api/41/resourceTables"
ANALYTICS_TABLES_ENDPOINT = "/api/41/resourceTables/analytics?skipResourceTables=true"


def get_request(url, auth):
    print(f"GET: {url}")
    response = requests.get(url, auth=auth)
    return response


def post_request(url, auth):
    print(f"POST: {url}")
    response = requests.post(url, auth=auth)
    return response


def execute_maintenance(base_url, auth):
    maintenance_url = f'{base_url}{MAINTENANCE_ENDPOINT}'
    response = post_request(maintenance_url, auth)

    if response.status_code == 200 or response.status_code == 204:
        print("Maintenance started successfully.")
        return True
    else:
        print(
            f"Error: Failed to start maintenance. Status code: {response.status_code}, Response: {response.text}")
        return False


def init_resource_generation(base_url, auth):
    """Initiate the creation of resource tables and return the task ID and notifier endpoint."""
    resource_table_url = f'{base_url}{RESOURCE_TABLES_ENDPOINT}'
    response = post_request(resource_table_url, auth)

    if response.status_code == 200:
        data = response.json()
        print("Resource table creation initiated.")
        task_id = data['response']['id']
        relative_endpoint = data['response']['relativeNotifierEndpoint']
        return task_id, relative_endpoint
    else:
        print(
            f"Error: Failed to initiate resource table creation. Status code: {response.status_code}, Response: {response.text}")
        return None, None


def check_status_messages(task_status_data):
    for item in task_status_data:
        print(item.get("message", ""))
        if "Resource tables generated: " in item.get("message", "") or "Analytics table updated" in item.get("message", ""):
            print("end")
            return True
    return False


def track_status(task_url, auth):
    """Track the status of a given task by periodically checking its status."""
    start_time = time.time()

    while True:
        if time.time() - start_time > MAX_WAIT_TIME:
            print("Error: The task took too long and is considered failed.")
            return False

        response = get_request(task_url, auth)

        if response.status_code == 200:
            task_status_data = response.json()
            if task_status_data == []:
                print("Task don't started.")
                time.sleep(CHECK_INTERVAL)
            elif check_status_messages(task_status_data):
                print("Task completed successfully.")
                return True
            else:
                print("Task not yet completed. Waiting for next check.")
                time.sleep(CHECK_INTERVAL)
        else:
            print(
                f"Error: Failed to fetch task status. Status code: {response.status_code}, Response: {response.text}")
            return False


def generate_analytics_tables(base_url, auth):
    """Initiate the creation of analytics tables and return the task ID and notifier endpoint."""
    analytics_table_url = f'{base_url}{ANALYTICS_TABLES_ENDPOINT}'
    response = post_request(analytics_table_url, auth)

    if response.status_code == 200:
        data = response.json()
        print("Analytics table creation initiated.")
        task_id = data['response']['id']
        relative_endpoint = data['response']['relativeNotifierEndpoint']
        return task_id, relative_endpoint
    else:
        print(
            f"Error: Failed to initiate analytics table creation. Status code: {response.status_code}, Response: {response.text}")
        return None, None


def main(username, password, server_url):
    """Main function to orchestrate the task execution and tracking."""
    base_url = f'{server_url}'
    auth = (username, password)

    if not execute_maintenance(base_url, auth):
        print("Exiting: Maintenance task failed.")
        return

    task_id, relative_endpoint = init_resource_generation(base_url, auth)
    if not task_id or not relative_endpoint:
        print("Exiting: Resource table creation task failed.")
        return

    task_status_url = f'{base_url}{relative_endpoint}'
    print(f"Tracking resource table task status at: {task_status_url}")

    if track_status(task_status_url, auth):
        print("Resource table creation completed successfully.")

        analytics_task_id, analytics_relative_endpoint = generate_analytics_tables(
            base_url, auth)
        if not analytics_task_id or not analytics_relative_endpoint:
            print("Exiting: Analytics table creation task failed.")
            return

        analytics_task_status_url = f'{base_url}{analytics_relative_endpoint}'
        print(
            f"Tracking analytics table task status at: {analytics_task_status_url}")

        if track_status(analytics_task_status_url, auth):
            print("All tasks completed successfully.")
        else:
            print("Exiting: Analytics table task tracking failed or timed out.")
    else:
        print("Exiting: Resource table task tracking failed or timed out.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DHIS2 API Task Automation")
    parser.add_argument('--user', required=True,
                        help="Username for authentication")
    parser.add_argument('--password', required=True,
                        help="Password for authentication")
    parser.add_argument('--server', required=True,
                        help="Base URL of the DHIS2 server (e.g., https://server/dhis2)")

    args = parser.parse_args()

    main(args.user, args.password, args.server)
