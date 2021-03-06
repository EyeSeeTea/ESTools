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


all_replaceable_objects = [
    "publicAccess",
    "userAccesses",
    "userGroupAccesses"
]


def main():
    args = get_args()
    dhis_objects = [item for item in args.apply if item not in args.exclude]
    if args.replace_objects:
        replaceable_objects = [item for item in args.replace_objects if item in all_replaceable_objects]
    else:
        replaceable_objects = all_replaceable_objects

    output = {}
    replacements = {}

    if args.replace_ids:
        replacements = get_replacements(args.replace_ids)

    input_objects = get_input_objects(args.input, args.exclude)

    for dhis_object in input_objects:
        dhis_object_old = json.load(open(args.input, encoding="utf-8")).get(dhis_object)

        if dhis_object in dhis_objects:
            if not dhis_object_old:
                print('WARN: Ignoring not found object %s' % dhis_object)
                continue

            elements_new = []
            for element in dhis_object_old:
                replace_objects(args, element, replaceable_objects)

                remove_ous_and_catcombos(args, dhis_object, element)

                replace_ids(args, element, replacements)

                elements_new.append(element)

            output[dhis_object] = elements_new
        else:
            output[dhis_object] = dhis_object_old

    json.dump(output, open(args.output, 'wt'), indent=2)


def replace_ids(args, element, replacements):
    if args.replace_ids and element['id'] in replacements.keys():
        element['id'] = replacements.get(element['id'])


def get_input_objects(input, excluded_objects):
    input_file = json.load(open(input, encoding="utf-8"))
    input_objects = [item for item in input_file.keys() if item not in excluded_objects]
    return input_objects


def get_replacements(ids):
    n = len(ids)
    if n % 2 != 0:
        sys.exit('Error: uneven number of ids to replace (%d), but ids should come '
                 'in pairs (from, to)' % n)
    else:
        replacements = dict([(ids[2 * i], ids[2 * i + 1]) for i in range(n // 2)])
    return replacements


def remove_ous_and_catcombos(args, dhis_object, element):
    if dhis_object in ['programs', 'dataElements']:
        if args.remove_ous and element.get('organisationUnits'):
            element['organisationUnits'] = []
        if args.remove_catcombos and element.get('categoryCombo'):
            del element['categoryCombo']


def replace_objects(args, element, replaceable_objects):
    for replaceable in replaceable_objects:
        if replaceable == "publicAccess":
            element['publicAccess'] = args.publicAccess
        elif replaceable in all_replaceable_objects:
            file = json.load(open(args.__getattribute__(replaceable)))
            element[replaceable] = file[replaceable]
        else:
            print("Error: " + replaceable + " is an invalid replaceable object)")
            print("List of valid replaceable objects: ")
            print(all_replaceable_objects)
            exit(0)


def get_args():
    "Return arguments"
    parser = argparse.ArgumentParser(description=__doc__)
    add = parser.add_argument  # shortcut
    add('-i', '--input', default="input.json",
        help='input file (read from input.json if not given)')
    add('-o', '--output', default="output.json",
        help='output file (write to output.json if not given)')
    add('-ua', '--userAccesses', dest="userAccesses", default="userAccesses.json",
        help='userAccesses file (read from userAccesses.json if not given)')
    add('-uga', '--userGroupAccesses', dest="userGroupAccesses", default="userGroupAccesses.json",
        help='userGroupAccesses file (read from userGroupAccesses.json if not given)')
    add('-ro', '--replace-objects', nargs='+', default=all_replaceable_objects,
        help='replace only the provided objects default: publicAccess, userAccesses, userGroupAccesses')
    add('--public-access', default='--------', dest="publicAccess",
        help='set public permissions. Default: no public access (--------)')
    add('--remove-ous', action='store_true',
        help='remove ous assignment from programs')
    add('--remove-catcombos', action='store_true',
        help='remove catcombos assignment from programs')
    add('--replace-ids', nargs='+', metavar='FROM TO', default=[],
        help='ids to replace. NOTE: references are not updated!!!')
    add('--apply-to-objects', dest='apply', nargs='+', default=dhis_objects,
        help='DHIS2 objects to include. Default: All')
    add('--exclude', nargs='+', default=[],
        help='DHIS2 objects to exclude. Default: None')
    return parser.parse_args()


if __name__ == '__main__':
    main()
