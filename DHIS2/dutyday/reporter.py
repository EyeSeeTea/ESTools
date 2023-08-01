import subprocess
import datetime
import sys
import subprocess
import json

import paramiko
#this script will be executed on local docker with vpn active
def execute_command_on_remote_machine(host, command):
    path_to_private_key = '/root/.ssh/id_rsa'  # ruta a tu archivo de clave privada SSH
    private_key = paramiko.RSAKey.from_private_key_file(path_to_private_key)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username="tomcatuser", pkey=private_key)

    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode().strip()

    client.close()

    return output

def ask_clone(host, file):
    result = execute_command_on_remote_machine(host, "/home/tomcatuser/bin/logger.sh clonelogger "+file)
    return result

def ask_monit(host):
    result = execute_command_on_remote_machine(host, "/home/tomcatuser/bin/logger.sh monitlogger")
    return result

def ask_db(host, file):
    result = execute_command_on_remote_machine(host, "/home/tomcatuser/bin/logger.sh databaselogger "+file)
    return result

def ask_analytics(host, logfile, server, type):
    if type == "docker":
        server = server + "-core"
        analyticslog = execute_command_on_remote_machine(host, "/home/tomcatuser/bin/logger.sh analyticslogger docker " + server + " " +logfile)
        return analyticslog
    elif type == "tomcat":
        analyticslog = execute_command_on_remote_machine(host, "/home/tomcatuser/bin/logger.sh analyticslogger tomcat " + server + " " +logfile)

        return analyticslog

    print('Informe generado.')

def runlogger(file):
    logger = ""
    with open(file, 'r') as file:
        data = json.load(file)
        for item in data:
            logger = logger + "\n"
            logger = logger + "Type: {"+item['type']+"}, Server: {"+item['server']+"}"
            logger = logger + "\n"
            # Accede a el Accede a elementos opcionales de manera segura
            url = item.get('url')
            if url:
                logger = logger + "URL: "+url
            logger = logger + "\n"
            if "backups" in item.keys():
                backups = item.get('backups')
                logger = logger + "\n"
                logger = logger + "Backups: "+ backups
                logger = logger + "\n"
                logger = logger + ask_db(item.get("host"), item.get("backups"))
                logger = logger + "\n"

            if "analytics" in item.keys():
                analytics = item.get('analytics')
                logger = logger + "\n"
                logger = logger + "Catalina: "+analytics
                logger = logger + "\n"
                logger = logger + ask_analytics(item.get("host"), item.get("analytics"), item.get("server"), item.get("type"))
                logger = logger + "\n"
            type = item.get('type')
            if type == "monit":
                monit = item.get('monit')
                logger = logger + "\n"
                logger = logger + "Monit: "+monit
                logger = logger + "\n"
                logger = logger + ask_monit(item.get("host"))
                logger = logger + "\n"

            if "cloning" in item.keys():
                logger = logger + "\n"
                logger = logger + "Monit: " + item.get("host")
                logger = logger + "\n"
                logger = logger + ask_clone(item.get("host"), item.get("cloning"))
                logger = logger + "\n"

            print('------')
            logger = logger + "\n"
            logger = logger + "\n"
    print(logger)


if __name__ == '__main__':
    runlogger('config.json')