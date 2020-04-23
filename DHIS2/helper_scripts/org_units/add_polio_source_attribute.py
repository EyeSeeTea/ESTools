import csv
import json

file = "luciaorgunit/organisationUnits_Botswana_Region_forImport.json"
national = "DHIS2 National Instance"
with open(file) as json_file:
    all_orgunits = json.load(json_file)
    new_list = list()
    for org_unit in all_orgunits["organisationUnits"]:
        import datetime

        date_object = datetime.date.today()
        date_object = "September 2019"
        value = national
        org_unit["attributeValues"] = [{"value": value + ", [" + str(date_object) + "]",
                             "attribute": {"id": "LmiNNUPlMxI", "name": "Org unit Source"}},
                            {"value": value + ", [" + str(date_object) + "]",
                             "attribute": {"id": "CxPTd6iKfUK", "name": "Shapefile source"}}]

with open(file, 'w') as outfile:
    json.dump(all_orgunits, outfile)

