
import json
import glob
import subprocess


file = "/home/idelcano/temp/ESTools/DHIS2/metadata_manipulation/fix_package/mal-epi-datasets-metadata-sync.json"
if True:
    print (file)
    with open(file, encoding='utf8') as json_file:
        objects = json.load(json_file)
        new_list = list()
        for key in objects.keys():
            uid_list = list()
            object_list = list()
            for object in objects[key]:
                if object["id"] not in uid_list:
                    uid_list.append(object["id"])
                    object_list.append(object)
                else:
                    print ("duplicate object key " + key)
                    print ("duplicate object " + object["id"] + " name:" +object["name"])
            objects[key] = object_list

    with open(file.replace(".json", "fixed.json"), 'w') as outfile:
        json.dump(objects, outfile, indent=4, ensure_ascii=False)