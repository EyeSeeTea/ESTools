import re
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
    print("----------------local update-------------")
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
    print(stderr.read().decode().strip())


    client.close()

    return output


def run_action(host, action, command=None):
    if action == "cloning":
        validate(host, action)
        return analyze_clone(host)
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


def remote_update(host, branch, proxy=""):
    print("trying to update"+ host["host"], host["logger_path"])
    file_path = host["logger_path"] + "logger.sh"
    command = file_path + " githubupdater " + host["logger_path"] + " " + branch + " " + proxy
    print(file_path)
    print(command)
    print("\n"+execute_command_on_remote_machine(host, command))


def analyze_clone(host):
    validate(host, "cloning")
    result = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh clonelogger "+validate(host,"cloning"))
    return result


def analyze_monit(host):
    result = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh monitlogger")
    return result


def analyze_catalina(host):
    result = execute_command_on_remote_machine(host, validate(host, "logger_path") + "logger.sh catalinaerrors "+validate(host, "catalina_file"))
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


def analyze_db(host):
    validate(host, "backups")
    result = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh databaselogger "+validate(host,"backups"))
    return result


def analyze_custom_script(host, command):
    result = execute_command_on_remote_machine(host, command)
    return result


def analyze_analytics(host):
    machine_type = host.get("type")
    logfile = host.get("analytics")
    if machine_type == "docker":
        docker_name = host.get("docker_name")
        analyticslog = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh analyticslogger docker " + logfile + " " +docker_name)
        return analyticslog
    elif machine_type == "tomcat":
        analyticslog = execute_command_on_remote_machine(host, validate(host,"logger_path") + "logger.sh analyticslogger tomcat " +logfile)

        return analyticslog

    print('Informe generado.')

def add_to_report(server, action, result, description):
    if server not in report_details.keys():
        report_details[server] = []
    report_details[server].append({action: {"result": result, "description": description}})


def load_host(server):
    server_name = server.get('server_name')
    temp_dict = {
        "server_name": server_name,
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
        "proxy": server.get('proxy')
    }
    hostdetails[server_name] = {k: v for k, v in temp_dict.items() if v is not None}


def load_servers(data):
    for server in data["servers"]:
        load_host(server)
        validate_host(hostdetails[server.get("server_name")])


def update_servers(data):
    print("----------------servers update-------------")
    for item in data["actions"]:
        if "github_update" == item.get("type"):
            for server in item.get("servers"):
                print("----------------Updating "+server+"-------------")
                branch = validate(data["config"], "branch")
                host = hostdetails[server]
                remote_update(host, branch, host.get("proxy"))
                print("----------------Updating "+server+" FINISHED-------------")


def remove_suffix(text):
    #remove proccess number
    cleaned_line = re.sub(r'(\[.*?)-\d+\]', r'\1]', text)
    #not remove final uid
    uid_match = re.search(r'(UID:[^\s]+)$', cleaned_line)
    if uid_match:
        uid = uid_match.group(0)
        cleaned_line = re.sub(r'(\[.*?\])(.*?)(UID:[^\s]+)$', r'\1 ' + uid, cleaned_line)
    else:
        #remove final token
        cleaned_line = re.sub(r'(\[.*?\]).*$', r'\1', cleaned_line)

        ultimo_indice = cleaned_line.rfind(')')
        if ultimo_indice != -1:
            cleaned_line = cleaned_line[:ultimo_indice + 2]

    return cleaned_line


def remove_excessive_info(log_text):
    pattern = re.compile(r'^(.{4}).*?nested exception is org\.postgresql\.util\.PSQLException: ERROR: (.*?)$', re.MULTILINE)

    cleaned_log = pattern.sub(r'\1\2', log_text)

    cleaned_log_response = re.sub(r'^.*Rule AMR_.*$', 'RULE ERROR IN AMR"', cleaned_log,
                          flags=re.MULTILINE)
    cleaned_log_response = re.sub(r'^.*Rule ETA.*$', 'RULE ERROR IN ETA"', cleaned_log_response,
                          flags=re.MULTILINE)
    cleaned_log = remove_suffix(cleaned_log_response)
    return cleaned_log


def check_servers():
    for server in hostdetails.keys():
        host = hostdetails[server]
        execute_command_on_remote_machine(host,  validate(host,"logger_path") + "logger.sh test_connection "+ validate(host, "server_name"))


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
                    result = run_action(hostdetails[server], "custom", item.get("command"))
                    add_to_report(server, "custom", result, item.get('description'))

            if "catalinaerrors" == item.get("type"):
                for server in item.get("servers"):
                    result = run_action(hostdetails[server], "catalinaerrors", hostdetails[server].get("catalina_file"))
                    add_to_report(server, "catalinaerrors", result, item.get('description'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Arguments --file: config file, --check-config check config file")
    
    parser.add_argument('--file', type=str, required=True, help='Path to the config file.')
    parser.add_argument('--check-config', action='store_true', help='Mode in to check the config file.')
    parser.add_argument('--check-servers', action='store_true', help='Mode in to check the server connection. ')
    parser.add_argument('--update', action='store_true', help='Update report and logger files.')
    parser.add_argument('--mode', type=str, help='Report mode print/printandpush/json/html', default="print")
    
    args = parser.parse_args()

    with open(args.file, 'r') as file:
        config = json.load(file)
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
            if args.mode == "json":
                print(json.dumps(report_details))
            elif args.mode == "print":
                for server in report_details.keys():
                    print("\n\n\n------------------------------------------------")
                    print("------------------------------------------------")
                    print("\n"+server+"\n")
                    for action_dict in report_details[server]:
                        for action_key,details in action_dict.items():
                            print("------------------------"+server+"-----------------------")
                            print("------------------------"+action_key+"-----------------------")
                            print(details.get("description","Empty description")+"\n")
                            print(details.get("result","Empty result")+"\n")
                            print("------------------------END-----------------------")
                    print("------------------------------------------------")
                    print("------------------------------------------------")
            
            elif args.mode == "html":
                print("<html><head><title>Report</title>")
                print("<style> #container { font-family: 'Courier New', Courier, monospace; margin: 20px; background-color: #f9f9f9; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); } .server h1, .action h3 { color: #333; background-color: #e9ecef; padding: 8px 12px; border-radius: 4px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); } .description p, .result p { color: #212529; background-color: #fff; padding: 8px 12px; margin-bottom: 8px; border: 1px solid #dee2e6; border-left-width: 5px; border-left-color: #007bff; border-radius: 4px; } .result p { border-left-color: #28a745; } span { color: red; } p { line-height: 1.5; } .result p, .description p { word-wrap: break-word; word-break: break-all; max-width: 100%; } </style>")
                print("<script> document.addEventListener('DOMContentLoaded', () => { const elements = document.querySelectorAll('.description p, .result p'); elements.forEach(element => { element.innerHTML = element.innerHTML.replace(/(\d+)%/g, (match, number) => { return number >= 90 && number <= 100 ? `<span style=\"color: red;\">${match}</span>` : match; }); element.innerHTML = element.innerHTML.replace(/(error)/gi, `<span style=\"color: red;\">$1</span>`); element.innerHTML = element.innerHTML.replace(/(OK)/g, `<span style=\"color: green;\">$1</span>`); }); }); </script>")
                print("</head><body>")
                for server in report_details.keys():
                    print("<div class='instance'> <div class='server'> <h1>" + server + "</h1>"+ "</div>")
                    for action_dict in report_details[server]:
                        for action_key,details in action_dict.items():
                            print("<div class='action'> <br><h3>" + action_key + "</h3></br>" + "</div>")
                            print("<div class='description'> <p>" + details.get("description","Empty description").replace("\n","<br/>") + "</p>"+ "</div>")
                            print("<div class='result'> <p>" + details.get("result","Empty result").replace("\n","<br/>") + "</p>"+ "</div>")
                    print("</div>")
                print("</body></html>")