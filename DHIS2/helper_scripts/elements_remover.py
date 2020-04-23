import json

files = ["coc_with_post.json", "coc_with_pre.json", "coc_without_post.json", "coc_without_pre.json"]

import csv
for json_file in files:
    with open(json_file) as json_f:
        print (json_file)
        all_elements = json.load(json_f)
        for element in all_elements["categoryOptions"]:
            del element["created"]
            del element["lastUpdated"]
            if "lastUpdatedBy" in element.keys():
                del element["lastUpdatedBy"]


        with open(json_file, 'w') as outfile:
            json.dump(all_elements, outfile, indent=4)