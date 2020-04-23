import json

file = "final_organisationUnits_CIV.json"
output_co = "final_organisationUnits_CIV.csv"

import csv

with open(file) as json_file:
    all_orgunits = json.load(json_file)
    new_list = list()
    with open(output_co, 'w', newline='') as file_co:
        writer_co = csv.writer(file_co)
        writer_co.writerow(["uid", "name", "shortName", "code", "openingDate", "level", "featureType", "coordinate"])
        for org_unit in all_orgunits["organisationUnits"]:
            coordinates = ""
            code = ""
            if "code" in org_unit.keys():
                code = org_unit["code"]
            if "coordinates" in org_unit.keys():
                coordinates = org_unit["coordinates"]
            writer_co.writerow(
                [org_unit["id"], org_unit["name"], org_unit["shortName"], code,
                 org_unit["openingDate"], org_unit["level"], org_unit["featureType"], coordinates])
