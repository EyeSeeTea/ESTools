import json
import subprocess
import sys


import argparse

from ESTools.DHIS2.cloner import dhis2api

categories_api_call = "/categories/%s?fields=name,categoryOptions[name,shortName,code]&paging=false"
organisation_units_api_call = "/organisationUnits?fields=id&filter=code:in:[%s]&paging=false&fields=organisationUnits[id]"
organisation_unit_group_api_call = "/organisationUnitGroups/%s.json"
key = ""
new_item = dict()


def main():

    global api

    args = get_args()
    cfg = get_config(args.config)
    output_file = cfg["config"]["output_file"]

    new_type = cfg["config"]["new_type"]

    user = cfg["config"]["user"]
    password = cfg["config"]["password"]
    url = cfg["config"]["url"]
    api = dhis2api.Dhis2Api(url, user, password)

    reference_type = cfg["config"]["reference_type"]
    reference_id = cfg["config"]["reference_id"]
    parent_type = cfg["config"]["parent_type"]
    parent_id = cfg["config"]["parent_id"]
    if reference_type == "categories":
        api_call = categories_api_call % reference_id
        key = "categoryOptions"


    referenced_json = api.get(api_call)[key]

    new_item = ""
    if parent_type == "organisationUnitGroups":
        key = "organisationUnits"
        organisation_units_code_list = [item["code"] for item in referenced_json]
        #Get orgunit ids from codes:
        api_call = organisation_units_api_call % ",".join(map(str, organisation_units_code_list))
        organisation_units_id_list = api.get(api_call)
        #Get parent organisationUnitGroup
        api_call = organisation_unit_group_api_call % parent_id
        organisation_unit_group_json = api.get(api_call)
        #assign new orgunit id list to orgunitgroup
        organisation_unit_group_json[key] = organisation_units_id_list[key]
        #format json
        new_item = {parent_type: [organisation_unit_group_json]}

    elif parent_type == "optionSet":
        count = 0
        new_item[new_type] = list()
        for item in referenced_json:
            count = count + 1
            new_item[new_type].append({"code": item["code"], "name": item["shortName"], "id": get_code(),
                                       "sortOrder": count, "optionSet": {"id": parent_id}, "favorites": [], "userGroupAccesses": []})



    with open(output_file, 'w')as outfile:
        json.dump(new_item, outfile, indent=True, ensure_ascii=False)


def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return str(output).replace("b'", "").replace("\\n'", "")


def get_args():
    "Return arguments"
    parser = argparse.ArgumentParser(description=__doc__)
    add = parser.add_argument  # shortcut
    add('-c', '--config', default="config.json", help='file with configuration')
    return parser.parse_args()


def get_config(fname):
    "Return dict with the options read from configuration file"
    print('Reading from config file %s ...' % fname)
    try:
        with open(fname) as f:
            config = json.load(f)
    except (AssertionError, IOError, ValueError) as e:
        sys.exit('Error reading config file %s: %s' % (fname, e))
    return config


if __name__ == '__main__':
    main()