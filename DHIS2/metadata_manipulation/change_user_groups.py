#/usr/bin/env python3
import json

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

for dhis_object in dhis_objects:
    dhis_object_old = json.load(open('input.json')).get(dhis_object)

    if not dhis_object_old:
        continue

    userGroupAccesses_new = json.load(open('userGroupAccesses.json'))['userGroupAccesses']


    elements_new = []
    for element in dhis_object_old:
        # Remove public access
        element['publicAccess'] = '--------'
        element['userGroupAccesses'] = userGroupAccesses_new
        elements_new.append(element)

    json.dump({dhis_object: elements_new}, open('results/%s.json' % dhis_object, 'wt'), indent=2)
