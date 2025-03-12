import json
import requests
import subprocess
from datetime import datetime, timezone

with open("config.json", "r") as file:
    config = json.load(file)

user_master = config["user_master"]
password_master = config["password_master"]
threshold_seconds = config["threshold_seconds"]
webhook_url = config["webhook_url"]
http_proxy = config.get("http_proxy", "")
https_proxy = config.get("https_proxy", "")
proxies = {
    "http": http_proxy if http_proxy else None,
    "https": https_proxy if https_proxy else None
}
servers = config["servers"]

def get_credentials(server):
    user = server.get("user") or user_master
    password = server.get("password") or password_master
    return user, password

def check_server(server):
    url = server["url"]
    name = server["name"]
    user, password = get_credentials(server)
    scheduler_url = f"{url}/api/scheduler"

    try:
        response = requests.get(scheduler_url, auth=(user, password),proxies=proxies, verify=True)
        response.raise_for_status()
        tasks = response.json()

        for task in tasks:
            if task.get("type") == "CONTINUOUS_ANALYTICS_TABLE":
                seconds_to_next = task.get("secondsToNextExecutionTime", 0)
                print(f"{name} {task.get('name', 'CONTINUOUS_ANALYTICS_TABLE')} {seconds_to_next}")

                print(task.get("status", []))
                if seconds_to_next < threshold_seconds and task.get("status", "") != "DISABLED":
                    print(f"Possible Issue detected in {url}: {seconds_to_next} seconds delay")
                    if task.get("status", "") != "RUNNING":
                        print(f"[ALERT] Issue detected in {url}: {seconds_to_next} seconds delay")
                        trigger_notification(name, url, seconds_to_next)

                        sequence = task.get("sequence", [])
                        job_id = sequence[0]["id"] if sequence else None
                        if not job_id:
                            print(f"[ERROR] The Continuous Analytics scheduler rule is broken on {name}")
                            continue
                        print("restart analytics")
                        restart_analytics(url, user, password, job_id)

    except requests.RequestException as e:
        print(f"[ERROR] Unable to connect to {url}: {e}")


def trigger_notification(server_name, server_url, seconds_to_next):
    title = f"{server_name} Continuous Analytics Delayed"
    content = f"\nServer: {server_url}\nDelay: {seconds_to_next} seconds\nThreshold: {threshold_seconds} seconds"

    try:
        subprocess.run(
            [
                "/usr/bin/python3", "webhook_notifier.py",
                "--webhook-url", webhook_url,
                "--title", title,
                "--content", content,
                "--http-proxy", http_proxy,
                "--https-proxy", https_proxy
            ],
            check=True
        )
        print(f"[OK] Notification sent for {server_name}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to execute notification script: {e}")

def restart_analytics(server_url, user, password, job_id):
    job_url = f"{server_url}/api/41/jobConfigurations/{job_id}/execute"

    headers = {
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Length": "0",
        "Origin": server_url,
        "Pragma": "no-cache",
        "Referer": f"{server_url}/dhis-web-scheduler/index.html",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.post(job_url, auth=(user, password), headers=headers, verify=True)
        response.raise_for_status()
        print(f"[OK] Restart command sent successfully to {server_url}")
    except requests.RequestException as e:
        print(f"[ERROR] Failed to restart analytics on {server_url}: {e}")


print(f"Start script at: {datetime.now(timezone.utc).strftime('%d-%m-%Y %H:%M:%S UTC')}")

for server in servers:
    check_server(server)