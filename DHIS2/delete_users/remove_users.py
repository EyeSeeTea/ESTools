import json
import requests
import subprocess
import threading
import sys

stop_event = threading.Event()

def delete_objects(json_file, api_endpoint, username, password, error_json_file_path, temp_log_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    
    error_objects = []

    # Extract IDs and send DELETE requests
    for item in data:
        object_id = item.get('id')
        if object_id:
            url = f"{api_endpoint}/{object_id}"
            response = requests.delete(url, auth=(username, password))
            if response.status_code in [200, 404, 409]:
                print(f"Object with ID {object_id} deleted successfully")
            else:
                message = f"ERROR: Failed to delete object with ID {object_id}. Status code: {response.status_code}"
                print(message)
                with open(temp_log_file, 'a') as log:
                    log.write(message + "\n")
                error_objects.append(item)

    # Write error objects to a different JSON file if there are users not deleted
    if error_objects:
        with open(error_json_file_path, 'w') as file:
            json.dump(error_objects, file, indent=4)

    return bool(error_objects)

def log_error_if_present(log_file_path, temp_log_file):
    # Tail dhis2 log
    cmd = ["tail", "-F", log_file_path]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    while True:
        output = process.stdout.readline()
        if "ERROR:  update or delete on table" in output:
            message = f"{output.strip()}"
            print(message)
            with open(temp_log_file, 'a') as log:
                log.write(message + "\n")

def execute_create_sql_query_script(temp_log_file, sql_output_file, user_to_takeover):
    subprocess.run(["python3", "create_sql_query.py", temp_log_file, sql_output_file, user_to_takeover])

def execute_sql_script(sql_output_file, image):
    subprocess.run(["d2-docker", "run-sql", "-i", image, sql_output_file])

def main():
    json_file_path = sys.argv[1] # Path to JSON file with users to be deleted. Example: users.json
    api_endpoint = sys.argv[2] # API endpoint DELETE users. Example: http://localhost:8080/api/38/users
    username = sys.argv[3] # API username
    password = sys.argv[4] # API password
    log_file_path = sys.argv[5] # Path to dhis2 log file 
    error_json_file_path = 'error_objects.json'  # Path to created JSON file containing not deleted users
    user_to_takeover = sys.argv[6] # User to use as new owner of the object
    image = sys.argv[7] # dhis2 image name
    temp_log_file = 'temp_log.txt' # Input file to generate sql
    sql_output_file = 'output.sql'  # Output sql file

    while True:
        # Create and start log thread
        log_thread = threading.Thread(target=log_error_if_present, args=(log_file_path, temp_log_file))
        log_thread.start()

        # Run delete_objects function
        has_errors = delete_objects(json_file_path, api_endpoint, username, password, error_json_file_path, temp_log_file)

        if not has_errors:
            print("INFO: All objects deleted successfully. Exiting.")
            # Stop the log thread
            stop_event.set()
            log_thread.join()
            break

        # Extract user IDs from failed deletes and create sql query to fix dependencies
        has_errors = execute_create_sql_query_script(temp_log_file, sql_output_file, user_to_takeover)

        # Execute sql script to fix dependencies
        has_errors = execute_sql_script(sql_output_file, image)

        # Use the error file as the input for the next iteration
        json_file_path = error_json_file_path

if __name__ == "__main__":
    main()
