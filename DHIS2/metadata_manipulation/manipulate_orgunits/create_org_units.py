import json
import subprocess
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

ADM_VIZ_NAME = "ADM"+"%s"+"_VIZ_NAME"
ADM_NAME_ALTERNATIVE = "ADM"+"%s"+"_NAME"
ADMIN_ALTERNATIVE = "ADM%s_NAME"
ADM_CODE = "ADM"+"%s"+"_CODE"
new_org = list()
admin0 = "GUINEA-BISSAU"
geojson_list = list()
def main():
    args = get_args()
    root_org_unit = "G9o5ad4oJJX"
    output_file = "GUINEA-BISSAU.json"
    level = 3
    for file in args.files:
        with open(file, encoding="utf-8") as json_file:
            admin_1_org_units = json.load(json_file)
            reference_id = level - 2
            parent_code = get_parent_code(level, reference_id)
            name_col = ADM_VIZ_NAME % (str(reference_id))
            name_col_alternative = ADMIN_ALTERNATIVE % (str(reference_id))
            code_col = ADM_CODE % (str(reference_id))

            for org_unit in admin_1_org_units["features"]:
                if org_unit["properties"]["ADM0_NAME"] == admin0:
                    if org_unit["properties"]["ENDDATE"] != "9999-12-31T00:00:00Z":
                        print (org_unit["properties"])
                    else:
                        geojson_list.append(org_unit)
                        create_org_unit(org_unit, name_col, name_col_alternative, code_col, level, parent_code, root_org_unit)
        level = level + 1

    with open(output_file, 'w') as outfile:
        json.dump({"organisationUnits": new_org}, outfile, indent=4, ensure_ascii=False)
    with open("geojson"+output_file, 'w') as outfile:
        json.dump(geojson_list, outfile, indent=4, ensure_ascii=False)


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


def create_org_unit(org_unit, name_col, name_col_alt, code_col, level, parent_col, root_org_unit):
    if org_unit["properties"]["ADM0_NAME"] == admin0:
        id = get_code()
        if name_col in org_unit.keys():
            if len(org_unit['properties'][name_col]) == 0:
                name_col = name_col_alt
        else:
            name_col = name_col_alt
        name = org_unit['properties'][name_col]
        short_name = org_unit['properties'][name_col]
        old_code = org_unit['properties'][code_col]
        code = org_unit['properties']["GUID"].replace("{","").replace("}","")
        geometry = org_unit['geometry']

        parent = root_org_unit
        import datetime
        date_object = datetime.date.today()
        formated_org_unit = {"id": id, "level": level, "name": name, "shortName": short_name,
                             "code": code, "leaf": False,
                             "old_code": old_code,
                             "geometry": geometry,
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