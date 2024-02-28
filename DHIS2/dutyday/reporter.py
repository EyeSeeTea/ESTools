import subprocess
import json

import paramiko
import argparse
import os

hostdetails = dict()
report_details = {}

def validate_host(host):
    validate(host, "server_name")
    validate(host, "url")
    validate(host, "user")
    validate(host, "host")


def validate(item, key):
    if key not in item.keys():
        raise ValueError(f"Key {key} not found in item {item}.")
    else:
        return item[key]


def local_update(config):
    branch = validate(config, "branch")
    path = validate(config, "path")
    try:
        subprocess.check_call(['python3', 'githubupdater.py', path, branch], cwd=path)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar repo_updater.py: {e}")


def remote_update(host, url, branch):
    print("\n"+execute_command_on_remote_machine(host, host["logger_path"] + "logger.sh githubupdater " + url + " " + branch))


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


def update_scripts(data):
    local_update(data["config"])
    update_servers(data)


#this script will be executed on local docker with vpn active

def execute_command_on_remote_machine(host, command):
    path_to_private_key = validate(host, "keyfile")
    private_key = paramiko.RSAKey.from_private_key_file(path_to_private_key)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(validate(host, "host"), username=validate(host, "user"), pkey=private_key)

    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode().strip()

    client.close()

    return output


def run_action(host, action):
    validate(host, action.type)
    if action.type == "cloning":
        return analyze_clone(host)
    elif action.type == "monit":
        return analyze_monit(host)
    elif action.type == "backups":
        return analyze_db(host)
    elif action.type == "analytics":
        return analyze_analytics(host)
    elif action.type == "custom":
        return analyze_custom_script(host, action.command)


def remote_update(host, url, branch):
    result = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh githubupdater "+url+" "+branch)
    return result


def analyze_clone(host):
    validate(host, "cloning")
    result = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh clonelogger "+validate(host,"cloning"))
    return result


def analyze_monit(host):
    result = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh monitlogger")
    return result


def analyze_db(host):
    validate(host, "backups")
    result = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh databaselogger "+validate(host,"backups"))
    return result


def analyze_custom_script(host, command):
    result = execute_command_on_remote_machine(host, command)
    return result


def analyze_analytics(host, logfile, docker_name, machine_type):
    if machine_type == "docker":
        analyticslog = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh analyticslogger docker " + server + " " +docker_name)
        return analyticslog
    elif machine_type == "tomcat":
        analyticslog = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh analyticslogger tomcat " +logfile)

        return analyticslog

    print('Informe generado.')

def add_to_report(server, action, result, description):
    if server not in report_details.keys():
        report_details.append({server: {}})
    report_details[server].append({action: {"result": result, "description": description}})


def load_host(server):
    server_name = server.get('server_name')
    type = server.get('type')
    tomcat = server.get('tomcat_folder')
    docker = server.get('docker_name')
    logger_path = server.get("logger_path")
    host = server.get('host')
    url = server.get('url')
    user = server.get('user')
    backups = server.get('backups')
    keyfile = server.get('keyfile')
    analytics = server.get('analytics')
    cloning = server.get('cloning')
    temp_dict = {
        "server_name": server_name,
        "type": type,
        "tomcat": tomcat,
        "docker": docker,
        "host": host,
        "url": url,
        "user": user,
        "backups": backups,
        "keyfile": keyfile,
        "logger_path": logger_path,
        "analytics": analytics,
        "cloning": cloning
    }
    hostdetails[server_name] = {k: v for k, v in temp_dict.items() if v is not None}


def load_servers(data):
    for server in data["servers"]:
        load_host(server)
        validate_host(hostdetails[server.get("server_name")])


def update_servers(data):
    for item in data["actions"]:
        if "github_update" == item.get("type"):
            for server in item.get("servers"):
                print("Updating "+server["server_name"])
                branch = validate(data["config"], "branch")
                url = validate(config["config"], "url")
                host = hostdetails[server]
                remote_update(host, url, branch)


def run_logger(data):
        for item in data["actions"]:
            if "backups" == item.get("type"):
                for server in item.get("servers"):
                    result = run_action(hostdetails[server], "backups")
                    add_to_report(server, "backups", result, item.get('description'))                    

            if "analytics" == item.get("type"):
                for server in item.get("servers"):
                    result = run_action(hostdetails[server], "analytics")
                    add_to_report(server, "analytics", result, item.get('description'))

            if "cloning" == item.get("type"):
                for server in item.get("servers"):
                    result = run_action(hostdetails[server], "cloning")
                    add_to_report(server, "cloning", result, item.get('description'))

            if "custom" == item.get("type"):
                for server in item.get("servers"):
                    result = run_action(hostdetails[server], "custom")
                    add_to_report(server, "custom", result, item.get('description'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Arguments --file: config file, --check check config file")
    
    parser.add_argument('--file', type=str, required=True, help='Path to the config file.')
    parser.add_argument('--check', action='store_true', help='Mode in to check the config file. Not required. ')
    parser.add_argument('--update', action='store_true', help='Update report and logger files ')
    parser.add_argument('--mode', type=str, help='Report mode print/printandpush/json/html ', default="print")
    
    args = parser.parse_args()

    with open(args.file, 'r') as file:
        config = json.load(file)
        if not args.check:
            load_servers(config)
        if args.check:
            validate_config(config)
        elif args.update:
            update_scripts(config)
        else:
            result = run_logger(config)
            if args.mode == "json":
                print(json.dumps(result))
            elif args.mode == "print":
                for server in result.keys():
                    print("\n\n\n------------------------------------------------")
                    print("------------------------------------------------")
                    print("\n"+server+"\n")
                    for action in result[server].keys():
                        print("------------------------Start_action-----------------------")
                        print(action.get("description")+"\n")
                        print(action.get("result")+"\n")
                        print("------------------------END-----------------------")
                    print("------------------------------------------------")
                    print("------------------------------------------------")
            
            elif args.mode == "html":
                print("<html><head><title>Report</title></head><body>")
                for server in result.keys():
                    print("<div class='instance'> <div class='server' <h1>" + server + "</h1>"+ "</div>")
                    for action in result[server].keys():
                        print("<div class='description' <p>" + action.get("description") + "</p>"+ "</div>")
                        print("<div class='result' <p>" + action.get("result") + "</p>"+ "</div>")
                    print("</div>")
                print("</body></html>")