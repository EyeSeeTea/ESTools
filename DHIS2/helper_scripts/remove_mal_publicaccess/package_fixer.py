
import json
import glob


files = glob.glob("/home/idelcano/temp/ESTools/DHIS2/metadata_manipulation/fix_package/pk/*.json")

for file in files:
    print (file)
    with open(file, encoding='utf8') as json_file:
        objects = json.load(json_file)
        new_list = list()
        for key in objects.keys():
            for object in objects[key]:
                    if "code" in object.keys() and object["code"] == "code":
                        print(object)
                        del object
                    if "publicAccess" in object.keys() and object["publicAccess"] != "--------":
                        object["userGroupAccesses"].append({"access": object["publicAccess"],
                                                            "userGroupUid": "OviFXqdot0H",
                                                            "displayName": "MAL_Malaria users",
                                                            "id": "OviFXqdot0H"})
                    object["publicAccess"] = "--------"

    with open(file.replace("/pk/", "/pk_out/"), 'w') as outfile:
        json.dump(objects, outfile, indent=4, ensure_ascii=False).encode('utf8')