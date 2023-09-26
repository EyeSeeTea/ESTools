# Delete WMR Form message spam

## Description

This folder contains two scripts:

- A python script by default checks for messages older than a week directed to a list of users whose subject contains 'WMR Form monitoring' and deletes them. The subject string and user list can be modified via parameters. These messages arrive in large numbers due to an error in a report.

- A shell script used to run the python script that gets the components necessary for the `dsn` parameter.

## Usage

The `delete_spam.py` script has the following parameters:

- `--uids`: A comma separated list of uids of users that received spam to delete. By default, the ones asked by the client.

- `--subject`:The pattern in the subject of the spam messages. By default, 'WMR Form monitoring%'.

- `--dsn`: String that describes the database connection, its a space separated list of item=value. The items are:

  - `host`: The hostname where the DB is.
  - `port`: The port where the DB can be reached.
  - `dbname`: The DB containing the messages.
  - `user`: The DB user to be used by the script.
  - `password`: The DB user password.

  By default it has the following value: 'host=localhost dbname=dhishq user=dhishq_usr'.

  Example:

  ```bash
  $ python3 ./delete_spam.py --dsn "host=localhost port=5432 dbname=dhis2 user=dhis"
  ```

---

The `run_delete_spam.sh` script has the following parameters:

- `conf_file`: The path to the DHIS2 conf file.
- `[docker_name]`: If the DHIS2 instance is hosted via docker images, this optional parameter will contain the instance DB docker container name (the name can be viewed via `docker ps`). To get access to the DB a `nc` tunnel will be created from the container internal DB port to the exposed port.

  Example:

  ```bash
  $ bash ./run_delete_spam.sh "/home/dhis/dhis.conf"
  ```

  Example for docker DHIS2 instance:

  ```bash
  $ bash ./run_delete_spam.sh "/home/dhis/dhis.conf" "dhis-2-38-db"
  ```
