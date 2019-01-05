"""
Enable and add roles to selected users.

Example:

    >> import dhis2api
    >> import process
    >> api = dhis2apis.Dhis2Api('http://localhost:8080/api',
                                username='admin', password='district')
    >> users = process.select_users(api, usernames=['test.dataentry'])
    >> process.add_roles(api, users, ['role1', 'role2'])
"""

import sys
import time
import requests

import dhis2api



def postprocess(cfg, entries):
    """Execute actions on the appropriate users as specified in entries.

    The entries structure looks like:
        [
            {
                "selectUsernames": ["test.dataentry"],
                "selectFromGroups": ["program1", "program2"],
                "action": "addRoles",
                "addRoles": ["role1", "role2"]
            }
        ]

    `action` can be "activate", "deleteOthers", "addRoles" or
    "addRolesFromTemplate", with an additional field for "addRoles" (a list)
    and "addRolesFromTemplate" (a string) if that's the action.
    """
    api = dhis2api.Dhis2Api(cfg['url'], cfg['username'], cfg['password'])

    wait_for_server(api)

    for entry in [expand_url(x) for x in entries]:
        execute(api, entry)


def expand_url(entry):
    if not is_url(entry):
        return entry
    else:
        try:
            return requests.get(x).json()
        except Exception as e:
            debug('Error on retrieving url with entries: %s - %s' % (entry, e))
            return {}


def is_url(x):
    return type(x) == str and x.startswith('http')


def execute(api, entry):
    "Execute the action described in one entry of the postprocessing"
    get = lambda x: entry.get(x, [])
    users = select_users(api, get('selectUsernames'), get('selectFromGroups'))
    debug('Users selected: %s' % ', '.join(get_username(x) for x in users))
    action = get('action')
    if action == 'activate':
        activate(api, users)
    elif action == 'deleteOthers':
        delete_others(api, users)
    elif action == 'addRoles':
        add_roles_by_name(api, users, get('addRoles'))
    elif action == 'addRolesFromTemplate':
        add_roles_from_template(api, users, get('addRolesFromTemplate'))


def wait_for_server(api, delay=30, timeout=300):
    "Sleep until server is ready to accept requests"
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


def select_users(api, usernames, users_from_group_names):
    "Return users with from usernames and from groups users_from_group_names"
    return unique(get_users_by_usernames(api, usernames) +
                  get_users_by_group_names(api, users_from_group_names))


def activate(api, users):
    for user in users:
        user['userCredentials']['disabled'] = False
        api.put('/users/' + user['id'], user)


def delete_others(api, users):
    "Delete all the users except the given ones and the one used by the api"
    usernames = [get_username(x) for x in users] + [api.username]
    uids_to_delete = api.get('/users', {
        'paging': False,
        'filter': 'userCredentials.username:!in:[%s]' % ','.join(usernames),
        'fields': 'id'})
    # Alternatively, we could get all the users with 'fields':
    # 'id,userCredentials[username]' and loop only over the ones whose
    # username is not in usernames.
    for uid in uids_to_delete:
        api.delete('/users/' + uid)


def add_roles_by_name(api, users, rolenames):
    "Add roles to the given users"
    roles_to_add = get_user_roles_by_name(api, rolenames)
    add_roles(api, users, roles_to_add)


def add_roles_from_template(api, users, template_with_roles):
    "Add roles in user template_with_roles to the given users"
    template = get_users_by_usernames(api, [template_with_roles])[0]
    roles_to_add = get_roles(template)
    add_roles(api, users, roles_to_add)


def add_roles(api, users, roles_to_add):
    for user in users:
        roles = unique(get_roles(user) + roles_to_add)
        user['userCredentials']['userRoles'] = roles
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
    "Return list of roles corresponding to the given role names"
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
