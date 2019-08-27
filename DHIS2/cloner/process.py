"""
Enable and add roles to selected users.

Example:

  import dhis2api
  import process
  api = dhis2api.Dhis2Api('http://localhost:8080/api',
                           username='admin', password='district')
  users = process.select_users(api, usernames=['test.dataentry'])
  process.add_roles(api, users, ['role1', 'role2'])
"""

import sys
import time
import requests
import json

import dhis2api


def postprocess(cfg, entries, import_dir):
    """Execute actions on the appropriate users as specified in entries.

    The entries structure looks like:
        [
            {
                "selectUsernames": ["test.dataentry"],
                "selectFromGroups": ["program1", "program2"],
                "action": "addRoles",
                "addRoles": ["role1", "role2"]
            },
            {
                "selectFiles": ["users.json"],
                "action": "import",
                "importStrategy": "CREATE_AND_UPDATE",
                "mergeMode": "MERGE",
                "skipSharing": "false"
             }
        ]

    `action` can be "activate", "deleteOthers", "addRoles" or
    "addRolesFromTemplate", with an additional field for "addRoles" (a list)
    and "addRolesFromTemplate" (a string) if that's the action.
    """
    api = dhis2api.Dhis2Api(cfg['url'], cfg['username'], cfg['password'])

    wait_for_server(api)

    for entry in [expand_url(x) for x in entries]:
        execute(api, entry, cfg, import_dir)


def expand_url(entry):
    if not is_url(entry):
        return entry
    else:
        try:
            return requests.get(entry).json()
        except Exception as e:
            debug('Error on retrieving url with entries: %s - %s' % (entry, e))
            return {}


def is_url(x):
    return type(x) == str and x.startswith('http')


def execute(api, entry, cfg, import_dir):
    "Execute the action described in one entry of the postprocessing"
    get = lambda x: entry.get(x, [])
    contains = lambda x: x in entry

    if contains('selectUsernames') or contains('selectFromGroups'):
        users = select_users(api, get('selectUsernames'), get('selectFromGroups'))
        debug('Users selected: %s' % ', '.join(get_username(x) for x in users))
        if not users:
            return
    elif contains('selectFiles'):
        files = ['%s/%s' % (import_dir, filename) for filename in get('selectFiles')]
        debug('Files selected: %s' % ', '.join(x for x in files))
    elif contains("selectServer"):
        servers = get('selectServer')
        debug('Servers selected: %s' % ', '.join(x for x in servers))
    else:
        debug('No selection.')
        return


    action = get('action')
    if action == 'activate':
        activate(api, users)
    elif action == 'deleteOthers':
        delete_others(api, users)
    elif action == 'addRoles':
        add_roles_by_name(api, users, get('addRoles'))
    elif action == 'addRolesFromTemplate':
        add_roles_from_template(api, users, get('addRolesFromTemplate'))
    elif action == 'import':
        import_json(api, files)
    elif action == 'changeServerName':
        change_server_name(api, get('changeServerName'))
    elif action == 'removeFromGroups':
        remove_groups(api, users, get('removeFromGroups'))
    else:
        raise ValueError('Unknown action: %s' % action)


def wait_for_server(api, delay=90, timeout=900):
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
    debug('Activating %d user(s)...' % len(users))
    for user in users:
        user['userCredentials']['disabled'] = False
        api.put('/users/' + user['id'], user)


def delete_others(api, users):
    "Delete all the users except the given ones and the one used by the api"
    usernames = [get_username(x) for x in users] + [api.username]
    users_to_delete = api.get('/users', {
        'paging': False,
        'filter': 'userCredentials.username:!in:[%s]' % ','.join(usernames),
        'fields': 'id,userCredentials[username]'})['users']
    # Alternatively, we could get all the users with 'fields':
    # 'id,userCredentials[username]' and loop only over the ones whose
    # username is not in usernames.
    debug('Deleting %d users...' % len(users_to_delete))
    users_deleted = []
    users_with_error = []
    for user in users_to_delete:
        try:
            api.delete('/users/' + user['id'])
            users_deleted.append(get_username(user))
        except requests.exceptions.HTTPError:
            users_with_error.append(get_username(user))
    if users_with_error:
        debug('Could not delete %d users: %s' %
              (len(users_with_error), users_with_error))


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
    debug('Adding %d roles to %d users...' % (len(roles_to_add), len(users)))
    for user in users:
        roles = unique(get_roles(user) + roles_to_add)
        user['userCredentials']['userRoles'] = roles
        api.put('/users/' + user['id'], user)


def remove_groups(api, users, groups_to_remove_from):
    debug('Removing %d users from %d groups...' %
          (len(users), len(groups_to_remove_from)))
    response = api.get('/userGroups', {
        'paging': False,
        'filter': 'name:in:[%s]' % ','.join(groups_to_remove_from),
        'fields': ('id,name,users')})
    for group in response['userGroups']:
        group['users'] = [user for user in group['users']
                          if user not in map(lambda element: pick(element, ['id']), users)]
        api.put('/userGroups/' + group['id'], group)


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


def import_json(api, files, importStrategy='CREATE_AND_UPDATE', mergeMode='MERGE',
                skipSharing='false'):
    "Import a json file into DHIS2"
    responses = {}
    for json_file in files:
        file_to_import = json.load(open(json_file))
        response = api.post('/metadata/', params={
            'importStrategy': importStrategy,
            'mergeMode': mergeMode,
            'skipSharing': skipSharing
        }, payload=file_to_import)
        summary = dhis2api.ImportSummary(response['stats'])
        debug('Import Summary for %s:' % json_file)
        debug('%s total: %s created - %s updated - %s deleted - %s ignored'
              % (summary.total, summary.created, summary.updated,
                 summary.deleted, summary.ignored))
        responses[json_file] = summary
    return responses


def change_server_name(api, new_name):
    debug('Changing server name to: %s' % new_name)

    if not new_name:
        debug('No new name provided - Cancelling server name change')
        return []

    response = api.post('/30/systemSettings/applicationTitle',
                        '%s' % ''.join(new_name), contenttype='text/plain')

    debug('change server result: %s' % response['message'])

    return response


def pick(element, properties):
    result = {}
    for property in properties:
        result[property] = element[property]
    return result


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
