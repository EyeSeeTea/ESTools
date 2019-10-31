#!/usr/bin/env python3

"""
Get a csv with all the dhis2 elements that contains the regexp in the name
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import json


def main():
    args = get_args()

    with open(args.output, mode='w') as file:
        csv_final_file = create_csv(file)

        user_group_id_name = create_groups_id_name_map(args)

        with open(args.input) as json_file:
            data = json.load(json_file)
            keys = data.keys()
            import re
            for key in keys:
                for item_row in data[key]:
                    if "name" not in item_row.keys():
                        print(key +" without name column: ")
                        print (item_row)
                    else:
                        if args.ignore_case:
                            match = re.search(args.reg_exp, item_row["name"], re.IGNORECASE)
                        else:
                            match = re.findall(args.reg_exp, item_row["name"])

                        item_row["usergroupnames"] = list()
                        if "userGroupAccesses" in item_row.keys():
                            for user in item_row["userGroupAccesses"]:
                                item_row["usergroupnames"].append(user_group_id_name[user["id"]])
                        if match:
                            csv_final_file.writerow([key, item_row["name"], item_row["id"], ' || '.join(item_row["usergroupnames"])])


def create_csv(file):
    import csv
    csv_final_file = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_final_file.writerow(['type', 'name', 'uid', 'usergroups'])
    return csv_final_file


def create_groups_id_name_map(args):
    user_group_id_name = dict()
    with open(args.user_groups_file) as json_file:
        data = json.load(json_file)
        for item_row in data['userGroups']:
            user_group_id_name[item_row["id"]] = item_row["name"]
    return user_group_id_name


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('-o', '--output', help='output file')
    add('-i', '--input', help='input metadata dhis2 json file')
    add('-r', '--reg-exp', help='regexp to find')
    add('--ignore-case', help='regexp to find', action='store_true')
    add('-u', '--user-groups-file', help='file with all the groups, Required to swap the user group id by names')

    return parser.parse_args()

if __name__ == '__main__':
    main()
