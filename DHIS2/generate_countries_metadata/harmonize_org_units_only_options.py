import json
import subprocess


def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return str(output).replace("b'", "").replace("\\n'", "")

new_options = list()
with open("country_options.json", encoding='utf8') as json_file:
    all_catoption = json.load(json_file)
    with open("organisationUnits_prod_without_na.json", encoding='utf8') as json_file:
        all_org_units = json.load(json_file)
        for org_unit in all_org_units["organisationUnits"]:
            print (org_unit["code"])
            exist = False
            for option in all_catoption["options"]:
                if option["name"] == org_unit["shortName"] or option["name"] == org_unit["name"]:
                    exist = True
                    if not option["code"].startswith("ALL"):
                        option["code"] = org_unit["code"]
                    option["id"] = get_code()
                    option["name"] = org_unit["shortName"]
                    option["optionSet"]={"id":"E1Extq4Q1he"}
                    new_options.append(option)
                    continue

            if not exist:
                uid = get_code()
                new_options.append({
                            "code": org_unit["code"],
                            "name": org_unit["shortName"],
                            "id": uid,
                            "optionSet": {
                                "id": "E1Extq4Q1he"
                            },
                            "favorites": [],
                            "attributeValues": [],
                            "translations": [],
                            "userAccesses": []
                        })

    with open("country_options_news_without_na.json", 'w')as outfile:
        json.dump({"options": new_options }, outfile, indent=True, ensure_ascii=False)