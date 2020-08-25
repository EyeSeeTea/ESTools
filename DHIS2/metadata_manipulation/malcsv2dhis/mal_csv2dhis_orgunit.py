import json
import subprocess
import json
import csv

{"id":"","name":"","shortName":"","code":"","featureType":"POINT","openingDate":"1970-01-01T00:00:00.000","coordinates":"","parent":{},"organisationUnitGroups":[{"id":"s5VT4a8awdc"}],"programs":[{"id":"G9hvxFI8AYC"},{"id":"Rw3oD4ExD8U"},{"id":"FUzFm6UEmRn"},{"id":"azxjVmQLicj"}]}


orgunit_list = list()


def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print(output)
    return str(output).replace("b'", "").replace("\\n'", "")


with open('/home/idelcano/EyeSeeTea/to_remove/ESTools/DHIS2/metadata_manipulation/malcsv2dhis/input/mal5.json') as f:
    data = json.load(f)
    with open('input/malawi.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                line_count += 1
                created = False
                for org_unit in data["organisationUnits"]:
                    if row[2] == org_unit["name"] or row[2] == org_unit["shortName"]:
                        coordinates = "["+row[9].replace(",",".")+","+row[8].replace(",",".")+"]"
                        if row[9] == "":
                            orgunit_list.append(
                            {"id": get_code(), "name": "SS-"+row[6], "shortName": row[6], "code": row[7], "featureType": "NONE",
                             "openingDate": "1970-01-01T00:00:00.000", "parent": { "id": org_unit["id"]},
                             "organisationUnitGroups": [{"id": "s5VT4a8awdc"}],
                             "programs": [{"id": "G9hvxFI8AYC"}, {"id": "Rw3oD4ExD8U"}, {"id": "FUzFm6UEmRn"},
                                          {"id": "azxjVmQLicj"}]})
                        else:
                            orgunit_list.append(
                            {"id": get_code(), "name": "SS-"+row[6], "shortName": row[6], "code": row[7], "featureType": "POINT",
                             "openingDate": "1970-01-01T00:00:00.000", "coordinates": coordinates, "parent": { "id": org_unit["id"]},
                             "organisationUnitGroups": [{"id": "s5VT4a8awdc"}],
                             "programs": [{"id": "G9hvxFI8AYC"}, {"id": "Rw3oD4ExD8U"}, {"id": "FUzFm6UEmRn"},
                                          {"id": "azxjVmQLicj"}]})
                        created = True
                        continue

                if not created:
                    print(f'\t{row[2]} works in the {row[6]} department, and was born in {row[7]}. {row[8]}{row[9]}')

        print(f'Processed {line_count} lines.')

        with open('mal_ss.json', 'w') as outfile:
            json.dump({ "organisationUnits": orgunit_list}, outfile)