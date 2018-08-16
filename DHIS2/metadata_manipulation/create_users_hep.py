#!/usr/bin/env python3

"""
Create a lot of data entry users for HEP.
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
import unicodedata
import json

import dhis2 as d2


def main():
    initialize_dhis2()

    countries = get_countries()
    users = []
    for country_name, country_id in countries:
        users.append(generate_user(country_name, country_id))
    print(json.dumps({'users': users}, indent=2))


def initialize_dhis2():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('-u', '--user', metavar='USER:PASSWORD', required=True,
        help='username and password for server authentication')
    add('--url-base', default='http://who-dev.essi.upc.edu:8081',
        help='base url to make queries')
    args = parser.parse_args()

    d2.USER = args.user
    d2.URLBASE = args.url_base.rstrip('/')


def get_countries():
    data = d2.get("organisationUnits.json?"
                  "level=3&fields=id,shortName&paging=false")
    return [(pretty_name(x['shortName']), x['id'])
            for x in data['organisationUnits']]


def pretty_name(name):
    name = remove_accents(name).lower().replace(',', '').replace(' ', '_')
    if '_(' in name:
        name = name.split('_(', 1)[0]
    return name


def remove_accents(name):
    return ''.join(c for c in unicodedata.normalize('NFD', name)
                   if unicodedata.category(c) != 'Mn')


def create_user(country_name, country_id):
    user = generate_user(country_name, country_id)
    print("Creating user for %s (%s): %s:%s (%s)" %
          (country_name, country_id, user['userCredentials']['username'],
           user['userCredentials']['password'], user['id']))
    data = d2.post("users", user)
    print("  %6s  %s" % (data['status'], data['stats']))


def generate_user(country_name, country_id):
    user_id = d2.generate_uid()
    user_creds_id = d2.generate_uid()
    username = country_name + ".dataentry"
    password = generate_password(country_name)
    return {
        'id': user_id,
        'firstName': "DataEntry Template",
        'surname': "HEP",
        'userCredentials': {
            'id': user_creds_id,
            'name': "DataEntry Template HEP",
            'displayName': "DataEntry Template HEP",
            'externalAuth': False,
            'externalAccess': False,
            'disabled': False,
            'invitation': False,
            'selfRegistered': False,
            'username': username,
            'password': password,
            'userInfo': {
                'id': user_id
            },
            'user': {
                'id': 'H4atNsEuKxP'
            },
            'userRoles': [
                { 'id': 'iWHyG5sDqRg' },
                { 'id': 'npKeda939aZ' },
                { 'id': 'PRR8faFzBmY' },
                { 'id': 'v0uKy6gA1YY' },
                { 'id': 'AgVHSpEo2pn' },
                { 'id': 'quenh5Es9sT' },
                { 'id': 'aanuJbyZXdj' }
            ]
        },
        'organisationUnits': [
            { 'id': country_id }
        ],
        'dataViewOrganisationUnits': [
            { 'id': 'H8RixfF8ugH' }
        ],
        'userGroups': [
            { 'id': 'uEYpW1usu0E' }
        ]
    }


def generate_password(name):
    if len(name) > 20 and '_' in name:
        name = name.split('_', 1)[0]
    return name.capitalize() + "2018!"



if __name__ == '__main__':
    main()
