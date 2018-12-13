#/usr/bin/env python3

"""
Change sharing settings on a json file
"""

import json
import argparse

dhis_objects = [
    "indicators",
    "indicatorGroups",
    "programIndicators",
    "options",
    "programRuleVariables",
    "programIndicators",
    "optionSets",
    "dataElements",
    "programStages",
    "programStageSections",
    "legendSets",
    "trackedEntityTypes"
]


def main():
    args = get_args()

    dhis_objects = [item for item in args.include if item not in args.exclude]
    output = {}

    for dhis_object in dhis_objects:
        dhis_object_old = json.load(open('input.json')).get(dhis_object)

        if not dhis_object_old:
            print('WARN: Ignoring not found object %s' % dhis_object)
            continue

        userGroupAccesses_new = json.load(open('userGroupAccesses.json'))['userGroupAccesses']

        elements_new = []
        for element in dhis_object_old:
            # Remove public access
            element['publicAccess'] = args.public_access
            element['userGroupAccesses'] = userGroupAccesses_new
            elements_new.append(element)

        output[dhis_object] = elements_new

    json.dump(output, open('output.json', 'wt'), indent=2)


def get_args():
    "Return arguments"
    parser = argparse.ArgumentParser(description=__doc__)
    add = parser.add_argument  # shortcut
    add('--public-access', default='--------', help='set public permissions. Default: no public access (--------)')
    add('--include', nargs='+', default=dhis_objects, help='DHIS2 objects to include. Default: All')
    add('--exclude', nargs='+', default=[], help='DHIS2 objects to exclude. Default: None')
    return parser.parse_args()

if __name__ == '__main__':
    main()