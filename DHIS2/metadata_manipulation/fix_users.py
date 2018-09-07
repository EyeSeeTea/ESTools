#!/usr/bin/env python3

"""

Take the metadata export from dev, export users, select the right users with
something like

  jcat users.json.zip --filters 'users:username:\.(validator|dataentry)$' -o users.json

and finally run this script to fix the users.

Possible ways to fix them:
* add the proper role and password.
* put the right dataViewOrganisationUnits
* put a nicer name
"""

import sys
import json
import unicodedata
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import dhis2 as d2


def main():
    args = parse_args()

    d2.USER = args.user
    d2.URLBASE = args.url_base.rstrip('/')

    users_file = args.file
    data = json.load(open(users_file))
    data_new = {'users': fix_users(data['users'])}
    print(json.dumps(data_new, indent=2))



def get_countries():
    data = d2.get("organisationUnits.json?"
                  "level=3&fields=id,shortName&paging=false")
    return [(pretty_name(x['shortName']), x['id'])
            for x in data['organisationUnits']]


def pretty_name(name):
    name = remove_accents(name)#.lower().replace(',', '').replace(' ', '_')
    if '_(' in name:
        name = name.split('_(', 1)[0]
    return name


def remove_accents(name):
    return ''.join(c for c in unicodedata.normalize('NFD', name)
                   if unicodedata.category(c) != 'Mn')


def fix_users(users):

    countries = {code: name for name, code in get_countries()}

    users_new = []
    for user in users:
        name = user['userCredentials']['username']

        if name == 'hep.validator':
            continue

        if name.endswith('.dataentry'):
            shortname = name[:-len('.dataentry')]
        elif name.endswith('.validator'):
            shortname = name[:-len('.validator')]
        else:
            raise RuntimeError('Unknown name: %s' % name)

        #password = generate_password(shortname)
        country_id = user['organisationUnits'][0]['id']
#        print(user['userCredentials']['username'], country_id)

        new_name = countries[country_id]

        fix_user(user, new_name, country_id)
        users_new.append(user)

    return users


def fix_user(user, new_name, country_id):
    creds = user['userCredentials']

    new_name += ' HEP ' + creds['username'].split('.')[1]

    user['dataViewOrganisationUnits'] = [{'id': country_id}]

    if user['firstName'].endswith('Template'):
        user['firstName'] = new_name
    if user['displayName'].endswith('Template HEP'):
        user['displayName'] = new_name
    # if user['surname'] == 'HEP':
    #     user['surname'] = new_name


    if creds['name'].endswith('Template HEP'):
        creds['name'] = new_name


def fix_user_example1(user, password):
    creds = user['userCredentials']
    creds['password'] = password
    creds['userRoles'].append({'id': 'LvNmqTiRq7u'})  # dashboard - all

    #user['userGroups'] = [{'id': 'uEYpW1usu0E'}]
    # This doesn't seem to do anything, we have to export the group
    # from dev and then import.


def generate_password(name):
    if len(name) > 15 and '_' in name:
        name = name.split('_', 1)[0]
    return name.capitalize() + "2018!"


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('-u', '--user', metavar='USER:PASSWORD', required=True,
        help='username and password for server authentication')
    add('--url-base', default='http://who-dev.essi.upc.edu:8081',
        help='base url to make queries')
    add('file', help='json file with the users to fix')
    return parser.parse_args()




if __name__ == '__main__':
    main()
