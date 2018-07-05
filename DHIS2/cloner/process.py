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
import json
import sys
import utils

import dhis2api

debug = utils.debug

class ProcessError(Exception):
    pass

def debug_users(msg, users):
    usernames_msg = ", ".join([user["userCredentials"]["username"] for user in users]) or "None"
    debug("{}: {}".format(msg, usernames_msg))

def get_users_by_group_names(api, user_group_names):
    debug("Get userGroups: name={}".format(", ".join(user_group_names)))
    response = api.get("/userGroups", {
        "paging": False,
        "filter": "name:in:[{0}]".format(",".join(user_group_names)),
        "fields": "id,name,users[:all,userCredentials[:all,userRoles[id,name]]]",
    })
    return utils.flatten(user_group["users"] for user_group in response["userGroups"])

def get_users_by_usernames(api, usernames):
    debug("Get users: username={}".format(", ".join(usernames)))
    response = api.get("/users", {
        "paging": False,
        "filter": "userCredentials.username:in:[{0}]".format(",".join(usernames)),
        "fields": ":all,userCredentials[:all,userRoles[id,name]]",
    })
    return response["users"]

def get_user_roles_by_name(api, user_role_names):
    debug("Get user roles: name={}".format(", ".join(user_role_names)))
    response = api.get("/userRoles", {
        "paging": False,
        "filter": "name:in:[{0}]".format(",".join(user_role_names)),
        "fields": ":all",
    })
    return response["userRoles"]

# Public interface

def enable_users(api, usernames=None, user_group_names=None):
    """Enable Dhis2 users by settings user.userCredentials.disabled = false."""
    users_from_user_groups = (get_users_by_group_names(api, user_group_names) if user_group_names else [])
    users_from_usernames = (get_users_by_usernames(api, usernames) if usernames else [])
    users = list(utils.unique(users_from_user_groups + users_from_usernames, lambda user: user["id"]))
    debug_users("Users to modify", users)

    for user in users:
        payload = {"id": user["id"], "userCredentials": {"disabled": False}}
        debug("Update user[username={0}]: {1}".format(user["userCredentials"]["username"], payload))
        api.patch("/users/{0}".format(user["id"]), payload)

    return users

def add_user_roles(api, entries):
    """
    Add user roles to all users within userGroups from userTemplate and extraUserRoles.

    Config structure example:

        [
            {
                "userGroups": ["_DATASET_M and E Officer"],
                "userTemplate": "district",
                "extraUserRoles": ["role1", "role2"]
            }
        ]
    """
    for entry in entries:
        user_groups_names = entry["userGroups"]
        user_template_username = entry["userTemplate"]
        extra_user_role_names = entry.get("extraUserRoles", [])

        user_templates = get_users_by_usernames(api, [user_template_username])
        if not user_templates:
            raise ProcessError("No user template found: {}".format(user_template_username))
        user_template = user_templates[0]
        users_in_user_groups = get_users_by_group_names(api, user_groups_names)
        user_roles_in_user_template = user_template["userCredentials"]["userRoles"]
        extra_user_roles = get_user_roles_by_name(api, extra_user_role_names)

        for user in users_in_user_groups:
            existing_user_roles = user["userCredentials"]["userRoles"]
            all_user_roles = utils.flatten([
                existing_user_roles,
                user_roles_in_user_template,
                extra_user_roles,
            ])
            unique_user_roles = list(utils.unique(all_user_roles, lambda user_role: user_role["id"]))
            user_roles_pathload = [{"id": ur["id"], "name": ur["name"]} for ur in unique_user_roles]
            user["userCredentials"]["userRoles"] = user_roles_pathload
            debug("Update user[username={0}]: setting {1} user roles \n{2}".format(
                user["userCredentials"]["username"],
                len(user["userCredentials"]["userRoles"]),
                "\n".join("  " + ur["name"] for ur in user["userCredentials"]["userRoles"]),
            ))
            api.put("/users/{0}".format(user["id"]), user)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='API endpoint URL')
    parser.add_argument('--username', required=True, help='API username')
    parser.add_argument('--password', required=True, help='API password')
    subparsers = parser.add_subparsers()

    parser_enable_users = subparsers.add_parser('enable-users', help='Enable users')
    parser_enable_users.add_argument('user_group_names', type=str, nargs='+', help='User group names')
    parser_enable_users.set_defaults(subparser="enable-users")

    parser_enable_users = subparsers.add_parser('add-user-roles', help='Add user roles to users')
    parser_enable_users.add_argument('add_user_roles_config_path', type=str, help='JSON config path')
    parser_enable_users.set_defaults(subparser="add-user-roles")

    args = parser.parse_args()
    api = dhis2api.Dhis2Api(args.url, args.username, args.password)

    if args.subparser == "enable-users":
        enable_users(api, user_group_names=args.user_group_names)
    elif args.subparser == "add-user-roles":
        with open(args.add_user_roles_config_path) as fd:
            config = json.load(fd)
        add_user_roles(api, config)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
