#!/usr/bin/env python
"""
DHIS2 API and helpers.

Example:

    >> import dhis2api
    >> api = dhis2api.Dhis2Api("http://localhost:8080/api", username="admin", password="district")
    >> dhis2api.enable_users(api, ["android", "district"])
"""
import argparse
import requests
import sys

DEBUG_ENABLED = True

class Dhis2Api:
    """
    Dhis2 API wrapper.

        >> api = Dhis2Api("http://localhost:8080/api", username="admin", password="district")
        >> api.get("/users")
        >> api.get("/users", {"fields": "id, displayName, created"})
        >> api.post("/users", ...)
    """
    def __init__(self, url, username="admin", password="district"):
        self.url = url.rstrip("/")
        self.auth = requests.auth.HTTPBasicAuth(username, password)

    def _get_url(self, path):
        return self.url + path

    def _request(self, method, path, **kwargs):
        url = self._get_url(path)
        request_method = getattr(requests, method)
        response = request_method(url, auth=self.auth, **kwargs)
        response.raise_for_status()
        return response.json()

    def get(self, path, params=None):
        return self._request("get", path, params=params)

    def post(self, path, payload):
        return self._request("post", path, json=payload)

    def put(self, path, payload):
        return self._request("put", path, json=payload)


class Dhis2ApiError(Exception):
    pass


def merge(d1, d2):
    """Merge d2 into d1 and return a new dictionary."""
    d3 = d1.copy()
    d3.update(d2)
    return d3

def debug(*args, **kwargs):
    """Print debug info to stderr."""
    if DEBUG_ENABLED:
        print(*args, file=sys.stderr, **kwargs)

def enable_users(api, usernames):
    """Enable Dhis2 users by settings user.userCredentials.disabled = false."""
    debug("GET users: {}".format(", ".join(usernames)))
    users_response = api.get("/users", {
        "filter": "userCredentials.username:in:[{0}]".format(",".join(usernames)),
        "fields": ":owner",
    })

    users = []
    for user in users_response["users"]:
        new_user_credentials = merge(user["userCredentials"], dict(disabled=False))
        new_user = merge(user, {"userCredentials": new_user_credentials})
        debug("PUT user[{username}]: disabled = {disabled}".format(**new_user_credentials))
        res = api.put("/users/{0}".format(user["id"]), new_user)
        if res["status"] != "OK":
            raise Dhis2ApiError("Error on PUT response: {}".format(str(res)))
        users.append(user)

    debug("Users updated: {}".format(", ".join([user["userCredentials"]["username"] for user in users])))
    return users

def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='API endpoint URL')
    parser.add_argument('--username', required=True, help='API username')
    parser.add_argument('--password', required=True, help='API password')

    subparsers = parser.add_subparsers()
    parser_enable_users = subparsers.add_parser('enable-users', help='Enable users')
    parser_enable_users.add_argument('usernames', type=str, nargs='+', help='Usernames')
    parser_enable_users.set_defaults(func=enable_users)

    args = parser.parse_args()

    api = Dhis2Api(args.url, args.username, args.password)
    args.func(api, args.usernames)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))