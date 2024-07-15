import json
import requests
import subprocess
import threading
import sys
import os
from dotenv import load_dotenv
#import time

load_dotenv()
stop_event = threading.Event()

def delete_objects(json_file, api_endpoint, username, password, error_json_file_path, temp_log_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    
    error_objects = []

    # Extract IDs and send DELETE requests
    for item in data:
        object_id = item.get('ID')
        if object_id:
            url = f"{api_endpoint}/{object_id}"
            response = requests.delete(url, auth=(username, password))
            if response.status_code == 200:
                print(f"Object with ID {object_id} deleted successfully")
            elif response.status_code == 409:
                print(f"Object with ID {object_id} has document attached and can not be deleted!")
                print()
            elif response.status_code == 404:
                print(f"Object with ID {object_id} not exists, skiping.")
            else:
                message = f"ERROR: Failed to delete object with ID {object_id}. Status code: {response.status_code}"
                print(message)
                with open(temp_log_file, 'a') as log:
                    log.write(message + "\n")
                error_objects.append(item)
            #time.sleep(1)  # Sleep for 1 second between API calls

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

def execute_init_sql_script(image, sql_init_file):
    subprocess.run(["d2-docker", "run-sql", "-i", image, sql_init_file])

def execute_sql_script(sql_output_file, image):
    subprocess.run(["d2-docker", "run-sql", "-i", image, sql_output_file])

def main():
    json_file_path = os.getenv('JSON_FILE_PATH') # Path to JSON file with users to be deleted. Example: users.json
    api_endpoint = os.getenv('API_ENDPOINT') # API endpoint DELETE users. Example: http://localhost:8080/api/38/users
    username = os.getenv('USERNAME') # API username
    password = os.getenv('PASSWD') # API password
    log_file_path = os.getenv('LOG_FILE_PATH') # Path to dhis2 log file 
    error_json_file_path = 'error_objects.json'  # Path to created JSON file containing not deleted users
    user_to_takeover = os.getenv('USER_TO_TAKEOVER') # User to use as new owner of the object
    image = os.getenv('DHIS2_DATA_IMAGE') # Dhis2 image name
    temp_log_file = 'temp_log.txt' # Input file to generate sql
    sql_output_file = 'output.sql'  # Output sql file
    sql_init_file = os.getenv('SQL_INIT_FILE') # Init sql file per instance

    while True:
        # Create and start log thread
        log_thread = threading.Thread(target=log_error_if_present, args=(log_file_path, temp_log_file))
        log_thread.start()

        # Run init sql script
        has_errors = execute_init_sql_script(image, sql_init_file)

        # Run delete_objects function
        has_errors = delete_objects(json_file_path, api_endpoint, username, password, error_json_file_path, temp_log_file)

        if not has_errors:
            print("INFO: All objects deleted successfully. Exiting.")
            # Stop the log thread
            stop_event.set()
            log_thread.join()
            sys.exit(0)

        # Extract user IDs from failed deletes and create sql query to fix dependencies
        has_errors = execute_create_sql_query_script(temp_log_file, sql_output_file, user_to_takeover)

        # Execute sql script to fix dependencies
        has_errors = execute_sql_script(sql_output_file, image)

        # Use the error file as the input for the next iteration
        json_file_path = error_json_file_path

if __name__ == "__main__":
    main()
