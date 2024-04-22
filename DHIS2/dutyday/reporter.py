import re
import subprocess
import json

import paramiko
import argparse
from datetime import datetime
from urllib.parse import quote
import requests
from requests.auth import HTTPBasicAuth

hostdetails = dict()
report_details = {}
server_config = {}
separator = "-------------------------------------"


def print_separator(separator, text=None):
    if text:
        half_separator = separator[:len(separator)//2]
        print(f"\n{half_separator}{text}{half_separator}")
    else:
        print(separator)


def validate(item, key):
    if key not in item.keys():
        raise ValueError(f"Key {key} not found in item {item}.")
    else:
        return item[key]


def validate_host(host):
    validate(host, "server_name")
    validate(host, "url")
    validate(host, "user")
    validate(host, "host")


def validate_config(config_file):
    servers = validate(config_file, "servers")
    for server in servers:
        validate_host(server)
    actions = validate(config_file, "actions")
    for action in actions:
        validate(action, "type")
        validate(action, "description")
        validate(action, "servers")
    config = validate(config_file, "config")
    validate(config, "url")
    validate(config, "branch")
    validate(config, "path")
    print("Config file is valid.")


def load_host(server):
    server_name = server.get('server_name')
    temp_dict = {
        "server_name": server_name,
        "categoryOptionCombo":  server.get('categoryOptionCombo'),
        "type": server.get('type'),
        "catalina_file": server.get('catalina_file'),
        "docker_name": server.get('docker_name'),
        "host": server.get('host'),
        "url": server.get('url'),
        "user": server.get('user'),
        "backups": server.get('backups'),
        "keyfile": server.get('keyfile'),
        "logger_path": server.get("logger_path"),
        "analytics": server.get('analytics'),
        "cloning": server.get('cloning'),
        "harborcloning": server.get('harborcloning'),
        "proxy": server.get('proxy')
    }
    hostdetails[server_name] = {k: v for k,
                                v in temp_dict.items() if v is not None}


def load_servers(data):
    for server in data["servers"]:
        load_host(server)
        validate_host(hostdetails[server.get("server_name")])


def load_server_config(config):
    config = validate(config, "report")
    if config.get("username", None) is None or config.get("password", None) is None or config.get("server", None) is None:
        print("Server, username and password are required to push the report")
        exit(1)
    elif config.get("orgUnit", None) is None:
        print("orgUnit are required to push the report")
        exit(1)
    else:
        server_config = {"username": config.get("username"),
                         "password": config.get("password"),
                         "server": config.get("server"),
                         "orgUnit": config.get("orgUnit"),
                         "proxy": config.get("proxy", None)}
        return server_config


def update_scripts(data):
    print_separator(separator, "Updating scripts")
    local_update(data["config"])
    update_servers(data)


def execute_command_on_remote_machine(host, command):
    path_to_private_key = validate(host, "keyfile")
    private_key = paramiko.RSAKey.from_private_key_file(path_to_private_key)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(validate(host, "host"), username=validate(
        host, "user"), pkey=private_key)

    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode().strip()
    print(stderr.read().decode().strip())

    client.close()

    return output


def run_action(host, action, command=None):
    if action == "cloning":
        validate(host, action)
        return analyze_clone(host)
    elif action == "harborcloning":
        validate(host, action)
        return analyze_harbor_clone(host)
    elif action == "monit":
        return analyze_monit(host)
    elif action == "backups":
        validate(host, action)
        return analyze_db(host)
    elif action == "analytics":
        validate(host, action)
        return analyze_analytics(host)
    elif action == "custom":
        return analyze_custom_script(host, command)
    elif action == "catalinaerrors":
        return analyze_catalina(host)


# this method output is printed always - not used by the report
def local_update(config):
    branch = validate(config, "branch")
    path = validate(config, "path")
    try:
        subprocess.check_call(
            ['python3', 'githubupdater.py', path, branch], cwd=path)
    except subprocess.CalledProcessError as e:
        print(f"Error executing repo_updater.py: {e}")


# this method output is printed always - not used by the report
def remote_update(host, branch, proxy=""):
    print("trying to update" + host["host"], host["logger_path"])
    file_path = host["logger_path"] + "logger.sh"
    command = file_path + " githubupdater " + \
        host["logger_path"] + " " + branch + " " + proxy
    print(file_path)
    print(command)
    print("\n"+execute_command_on_remote_machine(host, command))


# this method output is printed always - not used by the report
def update_servers(data):
    print_separator(separator, "Updating remote servers")
    for item in data["actions"]:
        if "github_update" == item.get("type"):
            for server in item.get("servers"):
                print_separator(separator, "Updating "+server)
                branch = validate(data["config"], "branch")
                host = hostdetails[server]
                remote_update(host, branch, host.get("proxy"))
                print_separator(separator, "Updating "+server+" finished")


def analyze_clone(host):
    validate(host, "cloning")
    result = execute_command_on_remote_machine(host, validate(
        host, "logger_path") + "logger.sh clonelogger "+validate(host, "cloning"))
    return result


def analyze_harbor_clone(host):
    validate(host, "harborcloning")
    result = execute_command_on_remote_machine(host, validate(
        host, "logger_path") + "logger.sh dockerharborclonelogger "+validate(host, "harborcloning"))
    return result


def analyze_monit(host):
    result = execute_command_on_remote_machine(
        host, validate(host, "logger_path") + "logger.sh monitlogger")
    return result


def analyze_db(host):
    validate(host, "backups")
    result = execute_command_on_remote_machine(host, validate(
        host, "logger_path") + "logger.sh databaselogger "+validate(host, "backups"))
    return result


def analyze_custom_script(host, command):
    result = execute_command_on_remote_machine(host, command)
    return result


def analyze_analytics(host):
    machine_type = host.get("type")
    logfile = host.get("analytics")
    if machine_type == "docker":
        docker_name = host.get("docker_name")
        analyticslog = execute_command_on_remote_machine(host, validate(
            host, "logger_path") + "logger.sh analyticslogger docker " + logfile + " " + docker_name)
        return analyticslog
    elif machine_type == "tomcat":
        analyticslog = execute_command_on_remote_machine(host, validate(
            host, "logger_path") + "logger.sh analyticslogger tomcat " + logfile)
        return analyticslog


def check_servers():
    for server in hostdetails.keys():
        host = hostdetails[server]
        server_name = validate(host, "server_name")
        print("checking server: " + server_name)
        execute_command_on_remote_machine(host,  validate(
            host, "logger_path") + "logger.sh test_connection " + server_name)

# this method is used to analyze the catalina logs removing the excessive info and counting the occurrences


def analyze_catalina(host):
    result = execute_command_on_remote_machine(host, validate(
        host, "logger_path") + "logger.sh catalinaerrors "+validate(host, "catalina_file"))
    lines = result.strip().split('\n')
    line_count = {}

    for line in lines:
        # Remove the first 31 characters
        line = remove_excessive_info(line[31:])

        # Add the line to the dictionary and count occurrences
        line_count[line] = line_count.get(line, 0) + 1

    # Create the new variable with unique lines and the number of occurrences
    new_content = ""
    for line, count in line_count.items():
        new_content += f"{count:03d} {line}\n"
    return new_content


# this method remove the suffix to make the logs line uniques by error
def remove_suffix(text):
    # remove proccess number
    cleaned_line = re.sub(r'(\[.*?)-\d+\]', r'\1]', text)
    # not remove final uid
    uid_match = re.search(r'(UID:[^\s]+)$', cleaned_line)
    if uid_match:
        uid = uid_match.group(0)
        cleaned_line = re.sub(
            r'(\[.*?\])(.*?)(UID:[^\s]+)$', r'\1 ' + uid, cleaned_line)
    else:
        # remove final token
        cleaned_line = re.sub(r'(\[.*?\]).*$', r'\1', cleaned_line)

        ultimo_indice = cleaned_line.rfind(')')
        if ultimo_indice != -1:
            cleaned_line = cleaned_line[:ultimo_indice + 2]

    return cleaned_line


# this method removes some hardcoded strings from the logs to make them more readable
def remove_excessive_info(log_text):
    pattern = re.compile(
        r'^(.{4}).*?nested exception is org\.postgresql\.util\.PSQLException: ERROR: (.*?)$', re.MULTILINE)

    cleaned_log = pattern.sub(r'\1\2', log_text)

    cleaned_log_response = re.sub(r'^.*Rule AMR_.*$', 'RULE ERROR IN AMR"', cleaned_log,
                                  flags=re.MULTILINE)
    cleaned_log_response = re.sub(r'^.*Rule ETA.*$', 'RULE ERROR IN ETA"', cleaned_log_response,
                                  flags=re.MULTILINE)
    cleaned_log_response = re.sub(r'^.*Rule Validate ETA_.*$', 'RULE ERROR IN ETA_"', cleaned_log_response,
                                  flags=re.MULTILINE)

    cleaned_log = remove_suffix(cleaned_log_response)
    return cleaned_log


def add_to_report(server, action, result):
    description = action.get("description")
    action_name = action.get("type")
    dataElement = action.get("dataElement")
    if server not in report_details.keys():
        report_details[server] = []
    report_details[server].append(
        {action_name: {"result": result, "description": description, "dataElement": dataElement}})


def pushReportToServer(categoryOptionCombo, dataElement, value):
    # escape firewall false positive
    value = value.replace("alter table", "altertable")
    data = {"dataValues": [
        {
            "dataElement": dataElement,
            "period": datetime.now().strftime('%Y%m%d'),
            "orgUnit": server_config.get("orgUnit"),
            "categoryOptionCombo": categoryOptionCombo,
            "attributeOptionCombo": "Xr12mI7VPn3",
            "value": value,
            "storedBy": "widp_script"
        }
    ]
    }

    url = server_config.get(
        "server") + '/api/dataValueSets.json'

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json'
    }
    print("Sending to: " + url)
    print("pushing coc:" + categoryOptionCombo + " dataelement: "+dataElement)
    print("result: "+result)

    if server_config.get("proxy", None):
        proxies = {
            'http': server_config.get("proxy"),
            'https': server_config.get("proxy"),
        }
        response = requests.post(url, json=data,
                                 auth=HTTPBasicAuth(server_config.get("username"), server_config.get("password")), proxies=proxies, headers=headers)
    else:
        response = requests.post(url, json=data,
                                 auth=HTTPBasicAuth(server_config.get("username"), server_config.get("password")), headers=headers)
    print(response.text)
    return response.status_code


def run_logger(data):
    for item in data["actions"]:
        if "backups" == item.get("type"):
            for server in item.get("servers"):
                result = run_action(hostdetails[server], "backups")
                add_to_report(server, item, result)

        if "analytics" == item.get("type"):
            for server in item.get("servers"):
                result = run_action(hostdetails[server], "analytics")
                add_to_report(server, item, result)

        if "cloning" == item.get("type"):
            for server in item.get("servers"):
                result = run_action(hostdetails[server], "cloning")
                add_to_report(server, item, result)

        if "harborcloning" == item.get("type"):
            for server in item.get("servers"):
                result = run_action(hostdetails[server], "harborcloning")
                add_to_report(server, item, result)

        if "custom" == item.get("type"):
            for server in item.get("servers"):
                result = run_action(
                    hostdetails[server], "custom", item.get("command"))
                add_to_report(server, item, result)

        if "catalinaerrors" == item.get("type"):
            for server in item.get("servers"):
                result = run_action(
                    hostdetails[server], "catalinaerrors", hostdetails[server].get("catalina_file"))
                add_to_report(server, item, result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="This Python script is designed for comprehensive management and reporting across multiple instances, streamlining analytics gathering, backup management, cloning result log, and system health monitoring via SSH connections. ")

    parser.add_argument('--file', type=str, required=True,
                        help='Path to the config file.')
    parser.add_argument('--check-config', action='store_true',
                        help='Mode in to check the config file.')
    parser.add_argument('--check-servers', action='store_true',
                        help='Mode in to check the server connection. ')
    parser.add_argument('--update', action='store_true',
                        help='Update report and logger files.')
    parser.add_argument('mode', type=str, choices=['print', 'json', 'html', 'push'],
                        help='Report mode to show the report')

    args = parser.parse_args()

    with open(args.file, 'r') as file:
        config = json.load(file)

    if args.mode == "push":
        server_config = load_server_config(config)
    if not args.check_config:
        load_servers(config)
    if args.check_config:
        validate_config(config)
    elif args.check_servers:
        check_servers()
    elif args.update:
        update_scripts(config)
    else:
        run_logger(config)
        if args.mode == "push":
            print("Pushing the report to the server")
            for server in report_details.keys():
                categoryOptionCombo = hostdetails[server].get(
                    "categoryOptionCombo")
                if categoryOptionCombo is not None:
                    for action_dict in report_details[server]:
                        for action_key, details in action_dict.items():
                            print(
                                f"Checking {action_key} data to the server")
                            dataElement = details.get("dataElement", None)
                            result = details.get("result", None)
                            if dataElement and result:
                                print(
                                    f"Pushing {action_key} data to the server")
                                status = pushReportToServer(
                                    categoryOptionCombo, dataElement, result)
                                if status != 200:
                                    print(
                                        f"Error pushing {action_key} data to the server: {status} ")

        elif args.mode == "json":
            print(json.dumps(report_details))
        elif args.mode == "print":
            for server in report_details.keys():
                print_separator(separator, None)
                print("\n\n\n")
                print_separator(separator, None)
                print_separator(separator, server)
                for action_dict in report_details[server]:
                    for action_key, details in action_dict.items():
                        print_separator(separator, server)
                        print_separator(separator, action_key)
                        print_separator(separator, details.get("description",
                                                               "Empty description"))
                        print(details.get("result",
                                          "Empty result"))
                        print_separator(separator, "End")
                    print_separator(separator, None)
                    print_separator(separator, None)

        elif args.mode == "html":
            print("<html><head><title>Report</title>")
            print("<style> #container { font-family: 'Courier New', Courier, monospace; margin: 20px; background-color: #f9f9f9; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); } .server h1, .action h3 { color: #333; background-color: #e9ecef; padding: 8px 12px; border-radius: 4px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); } .description p, .result p { color: #212529; background-color: #fff; padding: 8px 12px; margin-bottom: 8px; border: 1px solid #dee2e6; border-left-width: 5px; border-left-color: #007bff; border-radius: 4px; } .result p { border-left-color: #28a745; } span { color: red; } p { line-height: 1.5; } .result p, .description p { word-wrap: break-word; word-break: break-all; max-width: 100%; } </style>")
            print("<script> document.addEventListener('DOMContentLoaded', () => { const elements = document.querySelectorAll('.description p, .result p'); elements.forEach(element => { element.innerHTML = element.innerHTML.replace(/(\d+)%/g, (match, number) => { return number >= 90 && number <= 100 ? `<span style=\"color: red;\">${match}</span>` : match; }); element.innerHTML = element.innerHTML.replace(/(error)/gi, `<span style=\"color: red;\">$1</span>`); element.innerHTML = element.innerHTML.replace(/(OK)/g, `<span style=\"color: green;\">$1</span>`); }); }); </script>")
            print("</head><body>")
            for server in report_details.keys():
                print("<div class='instance'> <div class='server'> <h1>" +
                      server + "</h1>" + "</div>")
                for action_dict in report_details[server]:
                    for action_key, details in action_dict.items():
                        print("<div class='action'> <br><h3>" +
                              action_key + "</h3></br>" + "</div>")
                        print("<div class='description'> <p>" + details.get("description",
                                                                            "Empty description").replace("\n", "<br/>") + "</p>" + "</div>")
                        print("<div class='result'> <p>" + details.get("result",
                                                                       "Empty result").replace("\n", "<br/>") + "</p>" + "</div>")
                print("</div>")
            print("</body></html>")
