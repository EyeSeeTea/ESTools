#!/usr/bin/env python3

"""
Create a lot of data entry and validator users for HEP.
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
import unicodedata
import json

import dhis2 as d2


hep_countries = {
    "afghanistan",
    "albania",
    "algeria",
    "andorra",
    "angola",
    "antigua_and_barbuda",
    "argentina",
    "armenia",
    "australia",
    "azerbaijan",
    "bahamas",
    "bahrain",
    "bangladesh",
    "barbados",
    "belarus",
    "belize",
    "benin",
    "bhutan",
    "bosnia_and_herzegovina",
    "botswana",
    "brazil",
    "brunei_darussalam",
    "burkina_faso",
    "burundi",
    "cabo_verde",
    "cambodia",
    "cameroon",
    "canada",
    "central_african_republic",
    "chad",
    "chile",
    "china",
    "colombia",
    "comoros",
    "congo",
    "cook_islands",
    "costa_rica",
    "cote_d'ivoire",
    "cuba",
    "democratic_people's_republic_of_korea",
    "democratic_republic_of_the_congo",
    "djibouti",
    "dominica",
    "dominican_republic",
    "ecuador",
    "egypt",
    "el_salvador",
    "equatorial_guinea",
    "eritrea",
    "eswatini",
    "ethiopia",
    "fiji",
    "gabon",
    "gambia",
    "georgia",
    "ghana",
    "grenada",
    "guatemala",
    "guinea-bissau",
    "guinea",
    "guyana",
    "haiti",
    "honduras",
    "india",
    "indonesia",
    "iran",
    "iraq",
    "israel",
    "jamaica",
    "japan",
    "jordan",
    "kazakhstan",
    "kenya",
    "kiribati",
    "kuwait",
    "kyrgyzstan",
    "lao_people's_democratic_republic",
    "lebanon",
    "lesotho",
    "liberia",
    "libya",
    "madagascar",
    "malawi",
    "malaysia",
    "maldives",
    "mali",
    "marshall_islands",
    "mauritania",
    "mauritius",
    "mexico",
    "micronesia",
    "monaco",
    "mongolia",
    "montenegro",
    "morocco",
    "mozambique",
    "myanmar",
    "namibia",
    "nauru",
    "nepal",
    "new_zealand",
    "nicaragua",
    "niger",
    "nigeria",
    "niue",
    "oman",
    "pakistan",
    "palau",
    "panama",
    "papua_new_guinea",
    "paraguay",
    "peru",
    "philippines",
    "qatar",
    "republic_of_korea",
    "republic_of_moldova",
    "russian_federation",
    "rwanda",
    "saint_kitts_and_nevis",
    "saint_lucia",
    "saint_vincent_and_the_grenadines",
    "samoa",
    "san_marino",
    "sao_tome_and_principe",
    "saudi_arabia",
    "senegal",
    "serbia",
    "seychelles",
    "sierra_leone",
    "singapore",
    "solomon_islands",
    "somalia",
    "south_africa",
    "south_sudan",
    "sri_lanka",
    "sudan",
    "suriname",
    "switzerland",
    "syrian_arab_republic",
    "tajikistan",
    "thailand",
    "the_former_yugoslav_republic_of_macedonia",
    "timor-leste",
    "togo",
    "tonga",
    "trinidad_and_tobago",
    "tunisia",
    "turkey",
    "turkmenistan",
    "tuvalu",
    "uganda",
    "ukraine",
    "united_arab_emirates",
    "united_republic_of_tanzania",
    "united_states_of_america",
    "uruguay",
    "uzbekistan",
    "vanuatu",
    "venezuela",
    "viet_nam",
    "yemen",
    "zambia",
    "zimbabwe"}

existing_validators = {
    "mongolia"
    "indonesia"
    "georgia"
    "egypt"
    "rwanda"
    "brazil"}


def main():
    initialize_dhis2()

    countries = get_countries()

    #print_dataentry_users(countries)
    #print_validator_users(countries)
    # Uncomment your favorite


def print_dataentry_users(countries):
    users = []
    for country_name, country_id in countries:
        if country_name in hep_countries:
            users.append(generate_user_dataentry(country_name, country_id))
    print(json.dumps({'users': users}, indent=2))


def print_validator_users(countries):
    users = []
    for country_name, country_id in countries:
        if country_name in (hep_countries - existing_validators):
            users.append(generate_user_validator(country_name, country_id))
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
    print('Warning: modify the function before using it, if you '
          'know what you are doing. Could make users be not in '
          'sync across instances.')
    return
    user = generate_user(country_name, country_id)
    print("Creating user for %s (%s): %s:%s (%s)" %
          (country_name, country_id, user['userCredentials']['username'],
           user['userCredentials']['password'], user['id']))
    data = d2.post("users", user)
    print("  %6s  %s" % (data['status'], data['stats']))


def generate_user_dataentry(country_name, country_id):
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
            'access': {
                'delete': True,
                'externalize': True,
                'manage': True,
                'read': True,
                'update': True,
                'write': True
            },
            'userRoles': [
                { 'id': 'fKz9iwxYs28' },
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
            { 'id': 'uEYpW1usu0E' }  # though it doesn't add it
        ]
    }


def generate_user_validator(country_name, country_id):
    user_id = d2.generate_uid()
    user_creds_id = d2.generate_uid()
    username = country_name + ".validator"
    password = generate_password(country_name)
    return {
        'id': user_id,
        'firstName': "Validator Template",
        'surname': "HEP",
        'userCredentials': {
            'id': user_creds_id,
            'name': "DataEntry Template HEP",
            'displayName': "Validator Template HEP",
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
                'id': 'UFT4OT93GPZ'
            },
            'access': {
                'delete': True,
                'externalize': True,
                'manage': True,
                'read': True,
                'update': True,
                'write': True
            },
            'userRoles': [
                { 'id': 'AgVHSpEo2pn' },
                { 'id': 'ITUptKLtt6m' },
                { 'id': 'LvNmqTiRq7u' },
                { 'id': 'MI8nKpvLvqm' },
                { 'id': 'PRR8faFzBmY' },
                { 'id': 'aanuJbyZXdj' },
                { 'id': 'fKz9iwxYs28' },
                { 'id': 'iWHyG5sDqRg' },
                { 'id': 'mmARlr8lYP1' },
                { 'id': 'npKeda939aZ' },
                { 'id': 'v0uKy6gA1YY' },
                { 'id': 'vUD1FTSp8UB' }
            ]
        },
        'organisationUnits': [
            { 'id': country_id }
        ],
        'dataViewOrganisationUnits': [
            { 'id': country_id }
        ],
        'userGroups': [
            { 'id': 'xCbfjheBM6t' }  # though it doesn't add it
        ]
    }


def generate_password(name):
    if len(name) > 12 and '_' in name:
        # It'd be nicer with "> 20", but that's how we generated the old ones.
        name = name.split('_', 1)[0]
    return name.capitalize() + "2018!"



if __name__ == '__main__':
    main()
