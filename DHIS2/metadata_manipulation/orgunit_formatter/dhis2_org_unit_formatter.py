import json
import subprocess
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

ADM_VIZ_NAME = "ADM"+"%s"+"_VIZ_NAME"
ADM_CODE = "ADM"+"%s"+"_CODE"
new_org = list()

def main():
    args = get_args()
    root_org_unit = args.root
    output_file = args.output
    level = 4
    for file in args.files:
        with open(file) as json_file:
            admin_1_org_units = json.load(json_file)
            reference_id = level - 3
            parent_code = get_parent_code(level, reference_id)
            name_col = ADM_VIZ_NAME % (str(reference_id))
            code_col = ADM_CODE % (str(reference_id))

            for org_unit_admin_0 in admin_1_org_units["features"]:
                create_org_unit(org_unit_admin_0, name_col, code_col, level, parent_code, root_org_unit)
        level = level + 1

    with open(output_file, 'w') as outfile:
        json.dump({"organisationUnits": new_org}, outfile, indent=4)


def get_parent_code(level, reference_id):
    if level == 4:
        parent_code = None
    else:
        parent_id = reference_id - 1
        parent_code = ADM_CODE % (str(parent_id))
    return parent_code


def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print(output)
    return str(output).replace("b'", "").replace("\\n'", "")


def add_translation(org_unit, formated_org_unit, language, locale):
    if language in org_unit['properties'].keys():
        formated_org_unit["translations"].append({
            "property": "NAME",
            "locale": locale,
            "value": org_unit['properties'][language]
        })


def create_org_unit(org_unit, name_col, code_col, level, parent_col, root_org_unit):
    id = get_code()
    name = org_unit['properties'][name_col]
    short_name = org_unit['properties'][name_col]
    code = org_unit['properties'][code_col]
    type = org_unit['geometry']['type']
    if type == "MultiPolygon":
        featureType = "MULTI_POLYGON"
    elif type == "Polygon":
        featureType = "POLYGON"

    coordinates = str(org_unit['geometry']['coordinates']).replace(" ", "")
    parent = root_org_unit
    if parent_col is not None:
        for org_unit_formatted in new_org:
            if org_unit_formatted["code"] == org_unit['properties'][parent_col]:
                parent = org_unit_formatted["id"]
    import datetime
    date_object = datetime.date.today()
    formated_org_unit = {"id": id, "level": level, "name": name, "shortName": short_name,
                         "code": code, "leaf": False,
                         "featureType": featureType, "coordinates": coordinates,
                         "openingDate": "1970-01-01T00:00:00.000", "parent": {"id": parent},
                         "translations": [],
                         "attributeValues": [{"value": "Polio geodatabase, ["+str(date_object)+"]",
                                              "attribute": {"id": "LmiNNUPlMxI", "name": "Org unit Source"}},
                                             {"value": "Polio geodatabase, ["+str(date_object)+"]",
                                              "attribute": {"id": "CxPTd6iKfUK", "name": "Shapefile source"}}]}

    add_translation(org_unit, formated_org_unit, "ARABIC", "ar")
    add_translation(org_unit, formated_org_unit, "SPANISH", "sp")
    add_translation(org_unit, formated_org_unit, "FRENCH", "fr")
    add_translation(org_unit, formated_org_unit, "RUSSIAN", "ru")
    add_translation(org_unit, formated_org_unit, "CHINESE", "zh")

    new_org.append(formated_org_unit)


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('files', nargs='*', help='json files')
    add('-o', '--output', help='output file')
    add('-r', '--root', help='root uid')
    return parser.parse_args()


if __name__ == '__main__':
    main()
