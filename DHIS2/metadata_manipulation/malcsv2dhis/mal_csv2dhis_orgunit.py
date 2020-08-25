import json
import os
import subprocess
import json
import csv
import sys
from os import listdir
from os.path import isfile, join

from ESTools.DHIS2.metadata_manipulation.malcsv2dhis import dhis2api

orgunit_list = list()
output_dir = "output"
input_dir = "input"
# fields positions:
ss_name = 0
ss_code = 1
country = 2
admin1 = 3
admin2 = 4
admin3 = 5
latitude = 6
longitude = 7


def get_config(fname):
    "Return dict with the options read from configuration file"
    print('Reading from config file %s ...' % fname)
    try:
        with open(fname) as f:
            config = json.load(f)
    except (AssertionError, IOError, ValueError) as e:
        sys.exit('Error reading config file %s: %s' % (fname, e))
    return config


def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return str(output).replace("b'", "").replace("\\n'", "")


def main():
    cfg = get_config("config.json")
    user = cfg["user"]
    password = cfg["password"]
    server = cfg["server"]

    is_csv = lambda fname: os.path.splitext(fname)[-1] in ['.csv']
    is_not_csv = lambda fname: not os.path.splitext(fname)[-1] in ['.csv']
    is_not_git = lambda fname: not fname.startswith(".git")
    applied_filter = is_not_git if is_csv else is_not_csv

    files = [f for f in filter(applied_filter, listdir(input_dir)) if isfile(join(input_dir, f))]
    for path_file in files:
        orgunit_list = list()
        with open(os.path.join("input", path_file), encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                downloaded_country = ""
                server_org_unit = ""
                if line_count == 0:
                    print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    line_count += 1
                    api = dhis2api.Dhis2Api(server, user, password)
                    if downloaded_country != row[country]:
                        country_query = "/organisationUnits?filter=level:eq:%s&fields=name,shortName,id,path&filter=name:like:%s&paging=false" % (
                        "3", row[country])
                        data = api.get(country_query)
                        if len(data["organisationUnits"]) > 1:
                            print("the name is not unique: " + row[country])
                            print("query: " + country_query)
                            exit(1)
                        else:
                            downloaded_country = data["organisationUnits"][0]["id"]

                    server_org_unit = check_level(api, downloaded_country, row, server_org_unit, "6", admin3)

                    if server_org_unit == "":
                        server_org_unit = check_level(api, downloaded_country, row, server_org_unit, "5", admin2)

                    if server_org_unit == "":
                        server_org_unit = check_level(api, downloaded_country, row, server_org_unit, "4", admin1)

                    if server_org_unit == "":
                        print("org unit parent not found for ss: " + row[ss_name])
                        # Assign the country uid as parent if the org unit doesn't have any match
                        server_org_unit_id = downloaded_country
                    else:
                        server_org_unit_id = server_org_unit["id"]

                    coordinates = "[" + row[longitude].replace(",", ".") + "," + row[latitude].replace(",", ".") + "]"
                    if row[latitude] == "":
                        orgunit_list.append(
                            {"id": get_code(), "name": "SS-" + row[ss_name], "shortName": row[ss_name],
                             "code": row[ss_code],
                             "featureType": "NONE",
                             "openingDate": "1970-01-01T00:00:00.000", "parent": {"id": server_org_unit_id},
                             "organisationUnitGroups": [{"id": "s5VT4a8awdc"}],
                             "programs": [{"id": "G9hvxFI8AYC"}, {"id": "Rw3oD4ExD8U"}, {"id": "FUzFm6UEmRn"},
                                          {"id": "azxjVmQLicj"}]})
                    else:
                        orgunit_list.append(
                            {"id": get_code(), "name": "SS-" + row[ss_name], "shortName": row[ss_name],
                             "code": row[ss_code],
                             "featureType": "POINT",
                             "openingDate": "1970-01-01T00:00:00.000", "coordinates": coordinates,
                             "parent": {"id": server_org_unit_id},
                             "organisationUnitGroups": [{"id": "s5VT4a8awdc"}],
                             "programs": [{"id": "G9hvxFI8AYC"}, {"id": "Rw3oD4ExD8U"}, {"id": "FUzFm6UEmRn"},
                                          {"id": "azxjVmQLicj"}]})

        print(f'Processed {line_count} lines.')
        with open(join(output_dir, path_file.replace(".csv", "") + '.json'), 'w', encoding="utf-8") as outfile:
            json.dump({"organisationUnits": orgunit_list}, outfile, ensure_ascii=False)


def check_level(api, downloaded_country, row, server_org_unit, level, row_position):
    if row[row_position] is not "":
        country_query = "/organisationUnits?filter=path:like:%s/&filter=level:eq:%s&fields=name,shortName,id,path&paging=false" % (
            downloaded_country, level)
        data = api.get(country_query)
        for org_unit in data["organisationUnits"]:
            if org_unit["name"].lower() == row[row_position].lower() \
                    or org_unit["shortName"].lower() == row[row_position].lower():
                server_org_unit = data["organisationUnits"][0]
    return server_org_unit


if __name__ == '__main__':
    main()
