import argparse
import datetime
import json
import re
import subprocess


def read_last_notified_date(control_file_path):
    try:
        with open(control_file_path, 'r') as f:
            last_timestamp = float(f.read().strip())
            return datetime.datetime.fromtimestamp(last_timestamp)
    except (FileNotFoundError, ValueError):
        return datetime.datetime.min


def find_new_errors(log_file_path, log_string, last_notified_date):
    new_errors = []
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            if log_string in line:
                match = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', line)
                if match:
                    error_date = datetime.datetime.fromisoformat(match.group())
                    if error_date > last_notified_date:
                        new_errors.append((error_date, line.strip()))
    return new_errors


def update_control_file(control_file_path, new_last_date):
    with open(control_file_path, 'w') as f:
        f.write(str(new_last_date.timestamp()))


def notify_new_errors(ms_url, errors, control_file_path, notification_script_path):
    if errors:
        for error_date, error_msg in errors:
            message = f"Error found at {error_date}: {error_msg}"
            subprocess.run(
                ['/usr/bin/ruby', notification_script_path, ms_url, message], check=True)
        update_control_file(control_file_path, errors[-1][0])


def main(config_file_path):
    with open(config_file_path, 'r') as f:
        config = json.load(f)

    log_file_path = config['log_path']
    log_string = config['log_string']
    ms_url = config['ms_url']
    control_file_path = config['control_file']
    notification_script_path = config['notification_script_path']

    last_notified_date = read_last_notified_date(control_file_path)
    new_errors = find_new_errors(log_file_path, log_string, last_notified_date)
    notify_new_errors(ms_url, new_errors, control_file_path,
                      notification_script_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Log Notifier Script')
    parser.add_argument('config_file', type=str,
                        help='Path to the configuration JSON file')
    args = parser.parse_args()

    main(args.config_file)
