#!/usr/bin/env python3

"""
Create a lot of new users for NHWA training, with data read from
excel files, each one with its own format.
"""

import sys
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
import json
import unicodedata

import pandas as pd

import dhis2 as d2


ids = {}
group_ids = {
    "nhwa country team": 'vNDwT7P6thq',
    "health workforce team": 'fxyLXZ10TXC',
    "nhwa data completion": 'z6TJVUnop02',
    "nhwa global team": 'MVWS4lpbPo2',
    "nhwa regional team": 'ZWeEK9iBnEi'}
roles_ids = {
    "NHWA Landing Page": 'ohsWuKhHoA2',
    "NHWA Data Manager": 'hYMxwlLvfTy'}



def main():
    args = get_args()
    initialize_dhis2(args.user, args.url_base)

    fill_ids()

    countries = {
        'global': 'H8RixfF8ugH',
        'amro': 'wP2zKq0dDpw',
        'euro': 'svSQSBLTVz6'}
    countries.update(get_countries())
    for alias, country in [
            ('usa / hrsa', 'united states of america'),
            ('belize/trinidad & tobago', 'belize'),
            ('trinidad', 'trinidad and tobago'),
            ('usa', 'united states of america'),
    ]:
        countries[alias] = countries[country]

    #users = get_users_teena(countries) + get_users_aurora(countries)
    users = get_users_prod(countries)
    user_groups = [update_group(x, users) for x in group_ids.values()]

    fout = 'users_hwf.json'
    if os.path.exists(fout):
        answer = input('File %s already exists. Overwrite? [y/N] ' % fout)
        if not answer.lower().startswith('y'):
            sys.exit()
    with open(fout, 'wt') as f:
        f.write(json.dumps({'users': users, 'userGroups': user_groups},
                           indent=2) + '\n')


def fill_ids():
    global ids
    fname = 'users_hwf.json'
    if not os.path.exists(fname):
        sys.exit('Cannot get the uids from inexistent file: %s' % fname)
        # If you want to generate them instead for the first time, do
        # not use this function and uncomment the d2.generate_uid()
        # part later on.

    users = json.load(open('users_hwf.json'))['users']

    for user in users:
        username = user['userCredentials']['username']
        ids[username] = (user['id'], user['userCredentials']['id'])


def get_users_prod(countries):
    df = pd.read_excel(
        'InfoSystemsHRH_NHWA_GUARDS_DESK_LIST UPDATED_11_OCT.xlsx',
        'NHWAusers')
    users = []
    for i, row in enumerate(df.itertuples()):
        if i < 4:
            continue
        print(i)
        print(row)
        username = row[7]
        if username is pd.np.nan:
            continue
        default = lambda x: x.strip() if x is not pd.np.nan else username
        firstname = default(row[3])
        surname = default(row[2])
        name = (' '.join(x.strip() for x in [row[3], row[2]] if type(x) == str)
                or username)
        password = row[8]
        email = row[6]
        country = countries[row[1].lower()]
        groups = [group_ids[x.lower().strip()] for x in row[10].split(',')]
        users.append(generate_user(username, password,
                                   firstname, surname, name,
                                   email, country, groups))
    return users


def get_users_teena(countries):
    usernames_existing = ['i.dhillon']

    df = pd.read_excel('Copy of Participants-NHWA_5_Oct_tk.xlsx',
                       'Sheet2')
    users = []
    for row in df.itertuples():
        username = row[13]
        if username is pd.np.nan or username in usernames_existing:
            continue
        default = lambda x: x.strip() if x is not pd.np.nan else username
        firstname = default(row[2])
        surname = default(row[3])
        name = (' '.join(x.strip() for x in [row[2], row[3]] if type(x) == str)
                or username)
        password = row[15]
        email = row[4]
        country = countries[row[12].lower()]
        groups = [group_ids[x.lower().strip()] for x in row[17].split(',')]
        users.append(generate_user(username, password,
                                   firstname, surname, name,
                                   email, country, groups))
    return users


def get_users_aurora(countries):
    df = pd.read_excel('NHWA platform users euro training.xlsx',
                       'Sheet2')
    users = []
    for row in df.itertuples():
        username = row[6]
        password = row[7]
        name = row[2]
        firstname, surname = name.split(' ', 1)
        email = row[3]
        country = countries[row[5].lower()]
        groups = [group_ids[x.lower().strip()] for x in row[9].split(',')]
        users.append(generate_user(username, password,
                                   firstname, surname, name,
                                   email, country, groups))
    return users


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('-u', '--user', metavar='USER:PASSWORD', required=True,
        help='username and password for server authentication')
    add('--url-base', default='https://extranet.who.int/dhis2',
        help='base url to make queries')
    return parser.parse_args()


def initialize_dhis2(user, url_base):
    d2.USER = user
    d2.URLBASE = url_base.rstrip('/')


def get_countries():
    "Return dictionary {'country name': 'id'}"
    data = d2.get("organisationUnits.json?"
                  "level=3&fields=id,shortName&paging=false")
    return {pretty_name(x['shortName']): x['id']
            for x in data['organisationUnits']}


def pretty_name(name):
    name = remove_accents(name).lower()
    if ' (' in name:
        name = name.split(' (', 1)[0]
    return name


def remove_accents(name):
    return ''.join(c for c in unicodedata.normalize('NFD', name)
                   if unicodedata.category(c) != 'Mn')


def generate_user(username, password,
                  firstname, surname, name, email, orgunit, groups):
    global ids
    #user_id, user_creds_id = d2.generate_uid(), d2.generate_uid()
    user_id, user_creds_id = ids[username]

    user = {
        "id": user_id,
        "firstName": firstname,
        "surname": surname,
        "userCredentials": {
            "id": user_creds_id,
            "name": name,
            "displayName": name,
            "externalAuth": False,
            "externalAccess": False,
            "disabled": False,
            "invitation": False,
            "selfRegistered": False,
            "username": username,
            "password": password,
            "userInfo": {
                "id": user_id
            },
            "access": {
                "read": True,
                "update": True,
                "externalize": True,
                "delete": True,
                "write": True,
                "manage": True
            },
            "lastUpdatedBy": {
                "id": "UFT4OT93GPZ"
            },
            "user": {
                "id": "UFT4OT93GPZ"
            },
            "cogsDimensionConstraints": [],
            "catDimensionConstraints": [],
            "translations": [],
            "userGroupAccesses": [],
            "attributeValues": [],
            "userRoles": [
                {
                    "id": "ohsWuKhHoA2"
                },
                {
                    "id": "hYMxwlLvfTy"
                }
            ],
            "userAccesses": []
        },
        "attributeValues": [],
        "teiSearchOrganisationUnits": [],
        "organisationUnits": [
            {
                "id": orgunit
            }
        ],
        "userGroups": [{"id": x} for x in groups],
        "dataViewOrganisationUnits": [
            {
                "id": orgunit
            }
        ]
    }

    if type(email) == str:
        user['userCredentials']['email'] = email

    return user


def update_group(gid, users):
    "Add users to group with id gid"
    group = d2.get('userGroups/%s.json' % gid)
    def in_group(user):
        return any(x['id'] == gid for x in user['userGroups'])
    group['users'] = unique(group['users'] +
                            [{'id': x['id']} for x in users if in_group(x)])
    return group


def unique(xs):
    "Return a list of unique elements (as per their x['id']) in xs"
    seen = set()
    xs_unique = []
    for x in xs:
        if x['id'] not in seen:
            seen.add(x['id'])
            xs_unique.append(x)
    return xs_unique



if __name__ == '__main__':
    main()
