#/usr/bin/env python3

"""
Change sharing settings on a json file
"""

import json
import argparse
import sys

dhis_objects = [
    "indicators",
    "indicatorGroups",
    "programIndicators",
    "programIndicators",
    "optionSets",
    "dataElements",
    "programs",
    "programStages",
    "programStageSections",
    "legendSets",
    "trackedEntityTypes",
    "trackedEntityAttributes",
    "categories",
    "categoryCombos",
    "categoryOptionCombos",
    "categoryOptions"
]


def main():
    args = get_args()
    dhis_objects = [item for item in args.include if item not in args.exclude]
    output = {}
    replacements = {}

    if args.replace_ids:
        n = len(args.replace_ids)
        if n%2!=0:
            sys.exit('Error: uneven number of ids to replace (%d), but ids should come '
                     'in pairs (from, to)' % n)
        else:
            replacements = dict([(args.replace_ids[2 * i], args.replace_ids[2 * i + 1]) for i in range(n // 2)])

    input_file = json.load(open('input.json'))
    input_objects = [item for item in input_file.keys() if item not in args.exclude]
    for dhis_object in input_objects:
        dhis_object_old = json.load(open('input.json')).get(dhis_object)

        if dhis_object in dhis_objects:
            if not dhis_object_old:
                print('WARN: Ignoring not found object %s' % dhis_object)
                continue

            userAccesses_new = json.load(open('userAccesses.json'))['userAccesses']
            userGroupAccesses_new = json.load(open('userGroupAccesses.json'))['userGroupAccesses']

            elements_new = []
            for element in dhis_object_old:
                element['publicAccess'] = args.public_access
                element['userAccesses'] = userAccesses_new
                element['userGroupAccesses'] = userGroupAccesses_new

                if dhis_object in ['programs', 'dataElements']:
                    if args.remove_ous and element.get('organisationUnits'):
                        element['organisationUnits'] = []
                    if args.remove_catcombos and element.get('categoryCombo'):
                        del element['categoryCombo']

                if args.replace_ids and element['id'] in replacements.keys():
                    element['id'] = replacements.get(element['id'])

                elements_new.append(element)

            output[dhis_object] = elements_new
        else:
            output[dhis_object] = dhis_object_old

    json.dump(output, open('output.json', 'wt'), indent=2)


def get_args():
    "Return arguments"
    parser = argparse.ArgumentParser(description=__doc__)
    add = parser.add_argument  # shortcut
    add('--public-access', default='--------', help='set public permissions. Default: no public access (--------)')
    add('--remove-ous', action='store_true', help='remove ous assignment from programs')
    add('--remove-catcombos', action='store_true', help='remove catcombos assignment from programs')
    add('--replace-ids', nargs='+', metavar='FROM TO', default=[],
        help='ids to replace. NOTE: references are not updated!!!')
    add('--include', nargs='+', default=dhis_objects, help='DHIS2 objects to include. Default: All')
    add('--exclude', nargs='+', default=[], help='DHIS2 objects to exclude. Default: None')
    return parser.parse_args()


if __name__ == '__main__':
    main()
