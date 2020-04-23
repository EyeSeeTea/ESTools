import json

with open("metadata.json") as json_f:
    all_elements = json.load(json_f)
    for key in all_elements.keys():
        for item in all_elements[key]:
            item["name"]=""
            item["lastUpdated"]=""
            item["lastUpdatedBy"]=""

    with open("metadata.json", 'w') as outfile:
        json.dump(all_elements, outfile, indent=4)
