#!/usr/bin/env python3

"""
Get a description of a program.
"""

# The functions here are useful too in an interactive session, because
# we can use all the objects retrieved with get_object() without
# having to make any new query.

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import json


def main():
    args = get_args()
    group_uids = list()
    with open(args.user_groups_file) as json_file:
        data = json.load(json_file)
        for group in data['userGroups']:
            group_uids.append(group["id"])

    with open(args.input) as json_file:
        data = json.load(json_file)
        for key in args.objects:
            object_list = list()
            for object in data[key]:
                group_match = False
                other_group_match = False
                user_group_key = None
                if "userGroups" in object.keys():
                    user_group_key = "userGroups"
                elif "userGroupAccesses" in object.keys():
                    user_group_key ="userGroupAccesses"
                else:
                    print("object " +key+ "haven't usergroups")
                for group in object[user_group_key]:
                    if group["id"] in group_uids:
                        group_match = True
                    else:
                        other_group_match = True
                if group_match:
                    if other_group_match:
                        object["name"] = "gen_" + object["name"]
                    else:
                        object["name"] = args.prefix + object["name"]
                    object_list.append(object)
            result = {key: object_list}
            output = json.dumps(result, indent=4, sort_keys=True)
            open(args.output+"_"+key+".json", 'wt').write(output + '\n')


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('objects', nargs='*', help='name of the dhis2 object (ex. categories, dataElements')
    add('-o', '--output', help='output file')
    add('-i', '--input', help='input dhis2 json file')
    add('-u', '--user-groups-file', default=False, help='file with all the selected groups')
    add('-p', '--prefix', default="HWF", help='set the prefix')

    return parser.parse_args()

if __name__ == '__main__':
    main()
