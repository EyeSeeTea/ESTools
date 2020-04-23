import json

with open("microroles_prod.json") as json_file:
    all_orgunits = json.load(json_file)
    with open("microroles_dev2.json") as json_file_2:
        data = json.load(json_file_2)
        for dev in all_orgunits["userRoles"]:
            exist = False
            for prod in data["userRoles"]:
                if dev["id"] == prod["id"]:
                    exist = True
            if not exist:
                print (dev)