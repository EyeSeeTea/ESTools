Remove users from DHIS2 app

Scripts should be started on the server where dhis2 logs and dhis2 database are available.

Steps:

1. Download user list from "User extended app" using json format
2. Following arguments are required for the script to run:
```
    json_file_path = '<path/to/users.json>'  # Path to JSON file downloaded in step 1
    api_endpoint = '<https://host_name.com>'  # API endpoint to send DELETE call
    username = '<username>'  # API username
    password = '<password>'  # API user password
    log_file_path = '<path/to/log_file_path>'  # Path to dhis2 log file 
    user_to_takeover = '<new_user>'  # User to use as new owner of the object
    image = '<dhis2_image>'  # dhis2 image name
```
3. Run the script:
```
python -u remove_users.py <json_file_path> <api_endpoint> <username> <password> <log_file_path> <user_to_takeover> <image>
```
4. Run bash script clean_temp.sh to remove all temp files created
```
chmod +x clean_temp.sh && bash clean_temp.sh
```