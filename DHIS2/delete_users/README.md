Remove users from DHIS2 instnces

Scripts should be started on the server where dhis2 logs and dhis2 database are available.

Steps:

1. Download user list from "User extended app" using json format or convert existing csv to json
2. Create another csv file coping only ID column, use it only in step 3
3. Copy newly created csv file to dhis2 DB container to this path: /var/lib/postgresql/data/init.csv
4. Create .env file from .sample-env
5. Run the script:
```
python remove_users.py
```
6. Run bash script clean_temp.sh to remove all temp files created
```
chmod +x clean_temp.sh && bash clean_temp.sh
```