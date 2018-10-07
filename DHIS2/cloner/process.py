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


class ProcessError(Exception):
    pass


def debug_users(msg, users):
    unames = ', '.join([user['userCredentials']['username'] for user in users])
    debug('%s: %s' % (msg, unames or 'None'))


def get_users_by_group_names(api, user_group_names):
    debug('Get userGroups: name=%s' % ', '.join(user_group_names))
    response = api.get('/userGroups', {
        'paging': False,
        'filter': 'name:in:[%s]' % ','.join(user_group_names),
        'fields': ('id,name,'
                   'users[:all,userCredentials[:all,userRoles[id,name]]]')})
    return flatten(user_group['users'] for user_group in response['userGroups'])


def get_users_by_usernames(api, usernames):
    debug('Get users: username=%s' % ', '.join(usernames))
    response = api.get('/users', {
        'paging': False,
        'filter': 'userCredentials.username:in:[%s]' % ','.join(usernames),
        'fields': ':all,userCredentials[:all,userRoles[id,name]]'})
    return response['users']


def get_user_roles_by_name(api, user_role_names):
    debug('Get user roles: name=%s' % ', '.join(user_role_names))
    response = api.get('/userRoles', {
        'paging': False,
        'filter': 'name:in:[%s]' % ','.join(user_role_names),
        'fields': ':all'})
    return response['userRoles']


# Public interface.

def enable_users(api, usernames=None, user_group_names=None):
    "Enable Dhis2 users by settings user.userCredentials.disabled = false"
    users_from_user_groups = (get_users_by_group_names(api, user_group_names)
                              if user_group_names else [])
    users_from_usernames = (get_users_by_usernames(api, usernames)
                            if usernames else [])
    users = list(unique(users_from_user_groups + users_from_usernames,
                        lambda user: user['id']))
    debug_users('Users to modify', users)

    for user in users:
        payload = {'id': user['id'], 'userCredentials': {'disabled': False}}
        debug('Update user[username=%s]: %s' %
              (user['userCredentials']['username'], payload))
        api.patch('/users/' + user['id'], payload)

    return users


def add_user_roles(api, entries):
    """
    Add user roles to all users within userGroups from userTemplate and
    extraUserRoles.

    Config structure example:

        [
            {
                'userGroups': ['_DATASET_M and E Officer'],
                'userTemplate': 'district',
                'extraUserRoles': ['role1', 'role2']
            }
        ]
    """
    for entry in entries:
        user_groups_names = entry['userGroups']
        user_template_username = entry['userTemplate']
        extra_user_role_names = entry.get('extraUserRoles', [])

        user_templates = get_users_by_usernames(api, [user_template_username])
        if not user_templates:
            raise ProcessError('No user template found: ' + user_template_username)
        user_template = user_templates[0]
        users_in_user_groups = get_users_by_group_names(api, user_groups_names)
        user_roles_in_user_template = user_template['userCredentials']['userRoles']
        extra_user_roles = get_user_roles_by_name(api, extra_user_role_names)

        for user in users_in_user_groups:
            existing_user_roles = user['userCredentials']['userRoles']
            all_user_roles = flatten([
                existing_user_roles,
                user_roles_in_user_template,
                extra_user_roles])
            unique_user_roles = list(unique(all_user_roles,
                                            lambda user_role: user_role['id']))
            user_roles_pathload = [{'id': x['id'], 'name': x['name']}
                                   for x in unique_user_roles]
            user['userCredentials']['userRoles'] = user_roles_pathload
            debug('Update user[username=%s]: setting %s user roles \n%s' %
                  (user['userCredentials']['username'],
                   len(user['userCredentials']['userRoles']),
                   '\n'.join('  ' + ur['name']
                             for ur in user['userCredentials']['userRoles'])))
            api.put('/users/' + user['id'], user)


def flatten(xss):
    "Return flattened list of lists one level deep"
    return [x for xs in xss for x in xs]


def merge(d1, d2):
    "Return dictionary with the contents of d1 and d2 (shared keys from d2)"
    d3 = d1.copy()
    d3.update(d2)
    return d3


def debug(*args, **kwargs):
    "Print debug info to stderr"
    print(*args, file=sys.stderr, **kwargs)


def unique(sequence, tagger=None):
    "Return iterable of unique elements in sequence"
    tagger = tagger or (lambda x: x)
    seen = set()
    for item in sequence:
        tag = tagger(item)
        if tag not in seen:
            seen.add(tag)
            yield item
