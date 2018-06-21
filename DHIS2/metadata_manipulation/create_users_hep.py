#!/usr/bin/env python3

"""
Create a lot of data entry users for HEP.
"""

import random
import requests
import json
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt


def main():
    args = get_args()
    countries = get_countries(args)
    for country_name, country_id in countries[:5]:  ###
        post_user(args, country_name, country_id)


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('-u', '--user', help='user name and password for server authentication')
    add('--api-url', default='http://who-dev.essi.upc.edu:8081/api/',
        help='base url to make api queries')
    return parser.parse_args()


def get_countries(args):
    print("- Retrieving countries...")
    url = args.api_url + ('organisationUnits.json' +
                          '?level=3&fields=id,shortName&paging=false')
    user, passwd = args.user.split(':', 1)
    response = requests.get(url, auth=requests.auth.HTTPBasicAuth(user, passwd))
    data = json.loads(response.text)
    return [pretty_country(x) for x in data['organisationUnits']]


def pretty_country(country_dict):
    name = country_dict['shortName'].lower().replace(',', '').replace(' ', '_')
    return name, country_dict['id']


def post_user(args, country_name, country_id):
    print("- Creating user for %s (%s)..." % (country_name, country_id))
    user, passwd = args.user.split(':', 1)
    response = requests.post(args.api_url + 'users',
                             json=generate_user(country_name, country_id),
                             auth=requests.auth.HTTPBasicAuth(user, passwd))
    data = json.loads(response.text)
    print(data['status'])
    print(data['stats'])


def generate_user(country_name, country_id):
    data = {
        'user_id': generate_uid(),
        'user_creds_id': generate_uid(),
        'country_name': country_name,
        'country_Name': country_name.capitalize(),
        'country_id': country_id}
    return json.loads(user_template % data)


def generate_uid():
    "Return a uid that can be used for dhis2"
    # From the doc on "Generate identifieres" at
    # https://docs.dhis2.org/2.28/en/developer/html/webapi_system_resource.html
    # they need to be 11 A-Za-z0-9 characters long, starting with A-Za-z only.
    gen_chars = lambda c, n: ''.join(chr(i) for i in range(ord(c), ord(c)+n))
    AZaz = gen_chars('A', 26) + gen_chars('a', 26)
    AZaz09 = AZaz + gen_chars('0', 10)
    return (random.choice(AZaz) +
            ''.join(random.choice(AZaz09) for i in range(10)))



user_template = """\
{
    "id":"%(user_id)s",
    "firstName":"DataEntry Template",
    "surname":"HEP",
    "userCredentials":{
        "id":"%(user_creds_id)s",
        "name":"DataEntry Template HEP",
        "displayName":"DataEntry Template HEP",
        "externalAuth":false,
        "externalAccess":false,
        "disabled":false,
        "invitation":false,
        "selfRegistered":false,
        "username":"%(country_name)s.dataentry",
        "password":"%(country_Name)s2018!",
        "userInfo":{
            "id":"%(user_id)s"
        },
        "user":{
            "id":"H4atNsEuKxP"
        },
        "userRoles":[
            {
                "id":"iWHyG5sDqRg"
            },
            {
                "id":"npKeda939aZ"
            },
            {
                "id":"PRR8faFzBmY"
            },
            {
                "id":"v0uKy6gA1YY"
            },
            {
                "id":"AgVHSpEo2pn"
            },
            {
                "id":"quenh5Es9sT"
            },
            {
                "id":"aanuJbyZXdj"
            }
        ]
    },
    "organisationUnits":[
        {
            "id":"%(country_id)s"
        }
    ],
    "dataViewOrganisationUnits":[
        {
            "id":"H8RixfF8ugH"
        }
    ]
}
"""



if __name__ == '__main__':
    main()
