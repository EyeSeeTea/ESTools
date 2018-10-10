"""
DHIS2 API and helpers.

Example:

    >> import dhis2api
    >> import process
    >> api = dhis2apis.Dhis2Api('http://localhost:8080/api',
                                username='admin', password='district')
    >> process.enable_users(api, usernames=['android', 'district'],
                            user_group_names=['Administrators'])
"""

from __future__ import print_function

import sys
import time
import requests

import dhis2api



def postprocess(cfg, entries):
    """Add roles to the appropriate users as specified in entries.

    The entries structure looks like:
        [
            {
                "usernames": ["test.dataentry"],
                "fromGroups": ["program1", "program2"],
                "addRoles": ["role1", "role2"],
                "addRolesFromTemplate": "validator.template"
            }
        ]
    """
    api = dhis2api.Dhis2Api(cfg['url'], cfg['username'], cfg['password'])

    wait_for_server(api)

    for entry in entries:
        get = lambda x: entry.get(x, [])
        add_roles(api, get('usernames'), get('fromGroups'),
                  get('addRoles'), get('addRolesFromTemplate'))


def wait_for_server(api, delay=30, timeout=300):
    debug('Check active API: %s' % api.api_url)
    time.sleep(delay)  # in case tomcat is still starting
    start_time = time.time()
    while True:
        try:
            api.get('/me')
            break
        except requests.exceptions.ConnectionError:
            if time.time() - start_time > timeout:
                raise RuntimeError('Timeout: could not connect to the API')
            time.sleep(1)


def add_roles(api, usernames, users_from_group_names,
              rolenames, template_with_roles):
    """
    Take the users with the given usernames and all users in groups
    users_from_group_names, enable them and add them roles from
    add_roles and the roles in user add_roles_from_template.
    """
    users = unique(get_users_by_usernames(api, usernames) +
                   get_users_by_group_names(api, users_from_group_names))
    debug('Users to modify: %s' % ', '.join(get_username(x) for x in users))

    roles_to_add = get_user_roles_by_name(api, rolenames)
    if template_with_roles:
        template = get_users_by_usernames(api, [template_with_roles])[0]
        roles_to_add += get_roles(template)

    for user in users:
        roles = unique(get_roles(user) + roles_to_add)
        user['userCredentials']['userRoles'] = roles
        user['userCredentials']['disabled'] = False
        api.put('/users/' + user['id'], user)


def get_username(user):
    return user['userCredentials']['username']


def get_roles(user):
    return user['userCredentials']['userRoles']


def get_users_by_usernames(api, usernames):
    "Return list of users corresponding to the given usernames"
    debug('Get users: usernames=%s' % usernames)

    if not usernames:
        return []

    response = api.get('/users', {
        'paging': False,
        'filter': 'userCredentials.username:in:[%s]' % ','.join(usernames),
        'fields': ':all,userCredentials[:all,userRoles[id,name]]'})
    return response['users']


def get_users_by_group_names(api, user_group_names):
    "Return list of users belonging to any of the given user groups"
    debug('Get users from groups: names=%s' % user_group_names)

    if not user_group_names:
        return []

    response = api.get('/userGroups', {
        'paging': False,
        'filter': 'name:in:[%s]' % ','.join(user_group_names),
        'fields': ('id,name,'
                   'users[:all,userCredentials[:all,userRoles[id,name]]]')})
    return sum((x['users'] for x in response['userGroups']), [])


def get_user_roles_by_name(api, user_role_names):
    debug('Get user roles: name=%s' % user_role_names)
    response = api.get('/userRoles', {
        'paging': False,
        'filter': 'name:in:[%s]' % ','.join(user_role_names),
        'fields': ':all'})
    return response['userRoles']


def unique(xs):
    "Return list of unique elements in xs, based on their x['id'] value"
    xs_unique = []
    seen = set()
    for x in xs:
        if x['id'] not in seen:
            seen.add(x['id'])
            xs_unique.append(x)
    return xs_unique


def debug(txt):
    print(txt)
    sys.stdout.flush()
