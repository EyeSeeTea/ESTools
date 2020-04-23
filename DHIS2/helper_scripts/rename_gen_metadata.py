import csv
import json
import os

csv_file = "common_gen_2.csv"
json_file = "last_metadata_dev.json"
output_file = "downloaded_metadata_match"
lista = list()
entire_file = {}
files = list()
files.append(output_file)
import csv
eta = "Eta.json"
hep = "hep.json"
hwf = "hwf_modules.json"

import csv


def set_prefix(item, prefix):
    if "code" not in item.keys() or len(item["code"]) < 1:
        item["code"] = prefix + item["shortName"]
    else:
        item["code"] = prefix + item["code"]


def set_name(item, prefix):
    item["name"] = prefix + item["name"]


def set_public_access(item, item_action):
    if item_action["type"] == "categoryOptions":
        item["publicAccess"] = "r-rw----"
    if item_action["type"] == "categories":
        item["publicAccess"] = "r-------"
    if item_action["type"] == "categoryCombos":
        item["publicAccess"] = "r-------"
    if item_action["type"] == "categoryOptionGroups":
        item["publicAccess"] = "r-------"
    if item_action["type"] == "dataElementGroups":
        item["publicAccess"] = "r-------"
    if item_action["type"] == "dataElements":
        item["publicAccess"] = "r-------"
    if item_action["type"] == "legendSets":
        item["publicAccess"] = "r-------"
    if item_action["type"] == "optionSets":
        item["publicAccess"] = "r-------"


with open(csv_file) as csv_f:
    csv_reader = csv.reader(csv_f, delimiter=',')
    line_count = 0
    actions = list()

    for row in csv_reader:
        if line_count <= 1:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            actions.append({"id":row[2], "type":row[3], "prefix": row[4], "group": row[5]})

    with open(json_file) as json_f:
        all_elements = json.load(json_f)
        for key in all_elements.keys():
            print("key: "+key)
            new_elements = {key: []}
            lista = list()
            for item in all_elements[key]:
                for item_action in actions:
                    if item["id"] == item_action["id"] and item_action["type"] == key:
                        if key == "programRuleVariables":
                            item["name"] = "GEN_"+ item["name"]
                            new_elements[key].append(item)
                        if item_action["prefix"].upper() == "GEN_NTD" or item_action["prefix"].upper() == "NTD":
                            #if "userAccesses" in item.keys():
                            #    item["userAccesses"] = list()
                            #if key != "programRuleVariables":
                            #    print(item["code"])

                            if item_action["group"].upper() == "REMOVE_NHWA":
                                test = list()
                                with open(eta) as json_f2:
                                    json_f3 = json.load(json_f2)
                                    as_text = json.dumps(json_f3)
                                    if item["id"] in as_text:
                                        print("ALERT ETA! " + item["id"])
                                with open(hep) as json_f2:
                                    json_f3 = json.load(json_f2)
                                    as_text = json.dumps(json_f3)
                                    if item["id"] in as_text:
                                        print("ALERT HEP! " + item["id"])
                                with open(hwf) as json_f2:
                                    json_f3 = json.load(json_f2)
                                    as_text = json.dumps(json_f3)
                                    if item["id"] in as_text:
                                        print("ALERT hwf! " + item["id"])

                                new_usergroups = list()
                                for usergroup in item["userGroupAccesses"]:
                                    if (usergroup["displayName"].startswith("NHWA") or usergroup["displayName"].startswith(
                                            "ETA ") or usergroup["displayName"].startswith("HEP ")):
                                        None
                                    else:
                                        new_usergroups.append(usergroup)
                                item["userGroupAccesses"] = new_usergroups
                            elif item_action["group"].upper() == "REMOVE_NTD":
                                new_usergroups = list()
                                test = list()
                                for usergroup in item["userGroupAccesses"]:
                                    if usergroup["displayName"].startswith("SS_") or usergroup["displayName"].startswith("NTD_") \
                                            or usergroup["displayName"].startswith("NTD"):
                                        None
                                    else:
                                        if usergroup["displayName"] == "WIDP IT team":
                                            usergroup["access"] = "rw------"
                                        new_usergroups.append(usergroup)
                                item["userGroupAccesses"] = new_usergroups
                            new_elements[key].append(item)
            files.append(output_file + "_" + key + ".json")
            with open(output_file+"_"+key + ".json", 'w') as outfile:
                json.dump(new_elements, outfile, indent=4)

files_input = ""
for file in files:
    if file == "downloaded_metadata_match" or file == "downloaded_metadata_match_name":
        continue
    files_input = files_input + " " + file
print ("/home/idelcano/tmp/ESTools/DHIS2/metadata_manipulation/create_fake_datavalues/jcat.py "+ files_input + " -o " + output_file + ".json -s")
os.system("/home/idelcano/tmp/ESTools/DHIS2/metadata_manipulation/create_fake_datavalues/jcat.py "+ files_input + " -o " + output_file + ".json -s")
os.system("/home/idelcano/tmp/ESTools/DHIS2/metadata_manipulation/create_fake_datavalues/jcat.py " + output_file + ".json --stats")
