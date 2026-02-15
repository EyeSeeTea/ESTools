import json
import sys
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import argparse
import os
import logging

class DHIS2Monitor:
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)

        self.server = config.get('server')
        if self.server[-1:] != "/":
            self.server = self.server + "/"
            self.logger.debug(f"Adjusted base server URL to: {self.server}")

        self.auth = HTTPBasicAuth(config.get('user'), config.get('password'))

        self.filterGroup = config.get('filterGroup')
        if self.filterGroup:
            self.logger.debug(f"Filtering users by groups: {self.filterGroup}")
        else:
            self.logger.debug("No user group filtering applied.")
        months_expiry = config.get('months_expiry', 18)
        how_many_days = config.get('how_many_days', 7)
        self.expiry_beginning = (datetime.now() - relativedelta(months=months_expiry)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.expiry_end = (self.expiry_beginning + relativedelta(days=how_many_days)).replace(hour=23, minute=59, second=59, microsecond=0)
        self.logger.debug(f"Selecting dates between {self.expiry_beginning} and {self.expiry_end}")
        self.only_enabled = config.get('only_enabled', True)
        if self.only_enabled:
            self.logger.debug("Filtering only enabled users")
        else:
            self.logger.debug("All users will be considered (enabled and disabled)")
        self.webhook_url = config.get('webhook_url', None)
        if self.webhook_url:
            self.logger.debug("Webhook URL configured, notifications will be sent.")
            self.http_proxy = config.get('http_proxy', os.getenv("http_proxy", ""))
            self.https_proxy = config.get('https_proxy', os.getenv("https_proxy", ""))
            if self.http_proxy or self.https_proxy:
                self.logger.debug(f"Using proxies: HTTP: {self.http_proxy} / HTTPS: {self.https_proxy}")
            else:
                self.logger.debug("No proxies configured.")
            self.title = config.get('title', "DHIS2 Password Expiration Notification")
            self.destination = config.get('destination', "sysadmin")
        else:
            self.logger.debug("No webhook URL configured, notifications will not be sent.")

    def request(self, url):
        response = requests.get(url, auth=self.auth)
        return response

    def parse_dt(self, value=None):
        """Parses a datetime string avoiding milliseconds."""
        if not value:
            return None
        value = value.split(".")[0]
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

    def get_users_data(self):
        """Fetches the list of users and their userGroups."""
        return self.request(f'{self.server}api/users?fields=id,username,userGroups[name],created,passwordLastUpdated,disabled&paging=false')

    def filter_users(self, users):
        """Filters out users based on groups, whether the user is disabled and the password expiration time."""
        filtered = []
        for u in users:
            if self.only_enabled and u.get("disabled", False):
                continue
            if self.filterGroup:
                group_names = [g["name"] for g in u.get("userGroups", []) if "name" in g]
                if not set(group_names) & set(self.filterGroup):
                    continue
            pwdlast_dt = self.parse_dt(u.get("passwordLastUpdated"))
            created_dt = self.parse_dt(u.get("created"))
            if pwdlast_dt:
                if not (self.expiry_beginning <= pwdlast_dt <= self.expiry_end):
                    continue
                last_change = pwdlast_dt
            else:
                if not (created_dt and self.expiry_beginning <= created_dt <= self.expiry_end):
                    continue
                last_change = created_dt

            days_since = int((datetime.now() - last_change).total_seconds() / 86400)

            filtered.append({
                "id": u["id"],
                "username": u["username"],
                "days_since_change": days_since,
                "last_change": (pwdlast_dt or created_dt).isoformat(),
                "disabled": u.get("disabled")
            })

        return sorted(filtered, key=lambda x: x["username"])

    def handle_api_error(self, response):
        self.logger.error(f"API request failed: {response.status_code} - {response.headers} = {response.text[:500]}")
        sys.exit(0)

    def send_notification(self, content):
        proxies = {
            "http":  self.http_proxy,
            "https": self.https_proxy
        }

        payload = {"text": f"**{self.title}**\n{content}", "dest": f"{self.destination}"}
        try:
            response = requests.post(self.webhook_url, json=payload, headers={"Content-Type": "application/json"}, proxies=proxies, verify=True)
            response.raise_for_status()
            self.logger.info(f"[OK] Notification sent: {response.status_code}")
        except requests.RequestException as e:
            self.logger.error(f"Failed to send notification: {e}")


def main(config_path, debug=False):
    logging.basicConfig(
        level=logging.INFO if not debug else logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    print("Starting at: " + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

    with open(config_path, 'r') as conf_file:
        config_data = json.load(conf_file)

    monitor = DHIS2Monitor(config_data)

    response = monitor.get_users_data()
    
    if response.status_code != 200:
        monitor.handle_api_error(response)

    monitor.logger.debug(f"Found {len(response.json().get('users', []))} users in total. Checking for expiring passwords...")

    data_filtered = monitor.filter_users(response.json()["users"])

    if data_filtered:
        monitor.logger.info(f"Found {len(data_filtered)} users with expiring passwords during the current week:")
        monitor.logger.info(json.dumps(data_filtered, indent=4))
        if monitor.webhook_url:
            content = f"The following {len(data_filtered)} users have passwords that will expire during the current week:\n"
            for user in data_filtered:
                content += f"- {user['username']} ({user['last_change'][:10]})" + (f" [Disabled]" if user['disabled'] else "") + "\n"
            monitor.send_notification(content)
    else:
        monitor.logger.info("No users found with expiring passwords.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DHIS2 User password expiration notification script")
    parser.add_argument('--config', required=True, help="Config file path")
    parser.add_argument('--debug', action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    main(args.config, args.debug)
