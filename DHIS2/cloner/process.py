#!/usr/bin/env python
"""
DHIS2 API and helpers.

Example:

    >> import dhis2api
    >> api = dhis2apis.Dhis2Api("http://localhost:8080/api", username="admin", password="district")
    >> dhis2api.enable_users(api, usernames=["android", "district"], user_group_names=["Administrators"])
"""

from __future__ import print_function

import argparse
import sys
import utils

import dhis2api

debug = utils.debug

def debug_users(msg, users):
    usernames_msg = ", ".join([user["userCredentials"]["username"] for user in users]) or "None"
    debug("{}: {}".format(msg, usernames_msg))

def enable_users(api, usernames=None, user_group_names=None):
    """Enable Dhis2 users by settings user.userCredentials.disabled = false."""
    if user_group_names:
        debug("Get userGroups: name={}".format(", ".join(user_group_names)))
        ug_response = api.get("/userGroups", {
            "paging": False,
            "filter": "name:in:[{0}]".format(",".join(user_group_names)),
            "fields": "id,name,users[:owner]",
        })
        users_from_user_groups = utils.flatten(user_group["users"] for user_group in ug_response["userGroups"])
        debug_users("Users from user groups", users_from_user_groups)
    else:
        users_from_user_groups = []

    if usernames:
        debug("Get users: username={}".format(", ".join(usernames)))
        users_response = api.get("/users", {
            "paging": False,
            "filter": "userCredentials.username:in:[{0}]".format(",".join(usernames)),
            "fields": ":owner",
        })
        users_from_usernames = users_response["users"]
    else:
        users_from_usernames = []

    users = list(utils.unique(users_from_user_groups + users_from_usernames, lambda user: user["id"]))
    debug_users("Users to modify", users)

    for user in users:
        payload = {"id": user["id"], "userCredentials": {"disabled": False}}
        debug("PATCH user[username={0}]: {1}".format(user["userCredentials"]["username"], payload))
        api.patch("/users/{0}".format(user["id"]), payload)

    return users

def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='API endpoint URL')
    parser.add_argument('--username', required=True, help='API username')
    parser.add_argument('--password', required=True, help='API password')

    subparsers = parser.add_subparsers()
    parser_enable_users = subparsers.add_parser('enable-users', help='Enable users')
    parser_enable_users.add_argument('user_group_names', type=str, nargs='+', help='User group names')
    parser_enable_users.set_defaults(func=enable_users)

    args = parser.parse_args()

    api = dhis2api.Dhis2Api(args.url, args.username, args.password)
    args.func(api, user_group_names=args.user_group_names)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
