import json

with open("dev_roles_2.json") as json_file:
    all_orgunits = json.load(json_file)
    with open("2.30-micro-roles-1.0.11.json") as json_file_2:
        data = json.load(json_file_2)
        for dev in all_orgunits["userRoles"]:
            exist = False
            for prod in data["userRoles"]:
                if dev["id"] == prod["id"]:
                    exist = True
            if not exist:
                print(dev['id'])
                print (dev['name'])
                if "description" in dev.keys():
                    print(dev['description'])
                print("--------------------------")