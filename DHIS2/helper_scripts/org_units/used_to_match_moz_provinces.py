import csv
import json
uid_col=8
coor_col=6

with open("all_orgunits.json") as json_file:
    all_orgunits = json.load(json_file)
    with open("MOZ_provinces_organisationUnits.json") as json_file:
        data = json.load(json_file)
        for org_unit in data["organisationUnits"]:
            #org_unit.pop('geometry', None)
            #if "geometry" in org_unit.keys():
                #if "coordinates" in org_unit['geometry']:
                    #org_unit['coordinates'] = str(org_unit['geometry']['coordinates']).strip().replace(" ", "")
                    #org_unit['featureType'] = org_unit['geometry']['type'].upper()
                    #org_unit.pop('geometry', None)
            for server_ou in all_orgunits["organisationUnits"]:
                if server_ou["level"] == 4 and server_ou["name"].lower() == org_unit["name"].lower() \
                        or (server_ou["name"] == "Maputo" and org_unit["name"] == "MAPUTO PROVINCIA") \
                        or (server_ou["name"] == "Maputo City" and org_unit["name"] == "MAPUTO CIDADE"):
                    org_unit["shortName"] = org_unit["name"].title()
                    org_unit["name"] = org_unit["name"].title()
                    org_unit["old_id"] = org_unit["id"]
                    org_unit["id"] = server_ou["id"]
                    if "code" in server_ou.keys():
                        org_unit["code"] = server_ou["code"]
                    else:
                        print (org_unit)
                    #if "geometry" in org_unit.keys():
                    #    if "coordinates" in org_unit['geometry']:
                    #        org_unit['coordinates'] = org_unit['geometry']['coordinates']
                    #        org_unit['type'] = org_unit['geometry']['type'].upper()
                    #        org_unit['featureType'] = org_unit['geometry']['type'].upper()
                elif "shortName" not in org_unit.keys():
                    print(org_unit)
                    org_unit["shortName"] = org_unit["name"].title()
        with open("MOZ_provinces_organisationUnits_output.json", 'w') as outfile:
            json.dump(data, outfile)