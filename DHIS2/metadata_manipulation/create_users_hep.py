#!/usr/bin/env python3

"""
Create a lot of data entry users for HEP.
"""

import random
import json
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import dhis2 as d2


def main():
    initialize_dhis2()

    countries = get_countries()
    for country_name, country_id in countries:
        create_user(country_name, country_id)


def initialize_dhis2():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('-u', '--user', metavar='USER:PASSWORD', required=True,
        help='username and password for server authentication')
    add('--url-base', default='http://who-dev.essi.upc.edu:8081/',
        help='base url to make queries')
    args = parser.parse_args()

    d2.USER = args.user
    d2.URLBASE = args.url_base


def get_countries():
    print("Retrieving countries...")
    data = d2.get("organisationUnits.json?"
                  "level=3&fields=id,shortName&paging=false")
    return [pretty_country(x) for x in data['organisationUnits']]


def pretty_country(country_dict):
    name = country_dict['shortName'].lower().replace(',', '').replace(' ', '_')
    return name, country_dict['id']


def create_user(country_name, country_id):
    print("Creating user for %s (%s)..." % (country_name, country_id))
    data = d2.post("users", generate_user(country_name, country_id))
    print("  %6s  %s" % (data['status'], data['stats']))


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
    ],
    "userGroups":[
        {
            "id":"uEYpW1usu0E"
        }
    ]
}
"""



if __name__ == '__main__':
    main()
