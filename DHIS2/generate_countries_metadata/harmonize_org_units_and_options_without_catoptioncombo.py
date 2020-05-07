import json
import subprocess


def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return str(output).replace("b'", "").replace("\\n'", "")

new_catoptions = list()
new_catoptioncombo = list()
new_cat_combo = list()
new_category = list()
uid_list = list()
uid_catoption_list = list()
category = "hsdWMO0rhOF"
catcombo = "uzXwdArR9IP"
with open("categories_countries.json", encoding='utf8') as json_file:
    all_catoption = json.load(json_file)
    with open("organisationUnits_na_prod.json", encoding='utf8') as json_file:
        all_org_units = json.load(json_file)
        for org_unit in all_org_units["organisationUnits"]:
            print (org_unit["code"])
            exist = False
            for cat_option in all_catoption["categoryOptions"]:
                if cat_option["shortName"] == org_unit["shortName"] or cat_option["name"] == org_unit["name"] or cat_option["shortName"] == org_unit["name"] or cat_option["name"] == org_unit["shortName"]:
                    exist = True
                    catoptioncombo_uid = get_code()
                    if cat_option["publicAccess"] != "r-rw----":
                        cat_option["publicAccess"] = "r-rw----"
                    if not cat_option["code"].startswith("ALL"):
                        cat_option["code"] = "ALL_" + cat_option["code"]
                        cat_option["userGroupAccesses"].append(
                            {"access": "rw------", "userGroupUid": "UfhhwZK73Lg", "displayName": "WIDP IT team",
                             "id": "UfhhwZK73Lg"})
                    cat_option["name"] = org_unit["name"]
                    cat_option["shortName"] = org_unit["shortName"]
                    cat_option["categoryOptionGroups"].append("YBhkdOY83sW")
                    del cat_option["categories"]
                    new_catoptions.append(cat_option)
                    uid = cat_option["id"]
                    new_catoptioncombo.append(
                        {"id": catoptioncombo_uid, "name": org_unit["name"], "shortName": org_unit["shortName"],
                         "categoryCombo": {"id": catcombo}, "categoryOptions": [{"id": uid}]})
                    del cat_option["categoryOptionCombos"]
                    uid_list.append({"id": uid})
                    uid_catoption_list.append({"id": uid})
                    continue

            if not exist:
                uid = get_code()
                catoptioncombo_uid = get_code()
                new_catoptions.append({"code": "ALL_Op_Country_" + org_unit["code"], "id": uid, "name": org_unit["name"],
                                       "shortName": org_unit["shortName"], "publicAccess": "r-rw----",
                                       "userGroupAccesses": [{"access": "rw------","userGroupUid": "UfhhwZK73Lg","displayName": "WIDP IT team","id": "UfhhwZK73Lg"}], "attributeValues": [],
                                       "categoryOptionGroups": [{"id": "YBhkdOY83sW"}]})
                new_catoptioncombo.append({"id": catoptioncombo_uid,"name": org_unit["name"],"shortName": org_unit["name"],"categoryCombo": {"id": catcombo},"categoryOptions": [{"id": uid}]})
                uid_list.append({"id": uid})
                uid_catoption_list.append({"id": uid})

    with open("categories_countries_news_with_na_with_catcombo.json", 'w')as outfile:
        new_cat_combo.append(
            {"metadataType": "categoryCombos",
                "code": "All_Countries",
                "name": "Countries",
                "id": "uzXwdArR9IP",
                "dataDimensionType": "DISAGGREGATION",
                "displayName": "Countries",
                "publicAccess": "rw------",
                "translations": [],
                "userAccesses": [],
                "categories": []
            })
        new_category.append(
            {
                "metadataType": "categories",
                "code": "All_countries",
                "lastUpdated": "2020-04-28T11:14:02.095",
                "id": "hsdWMO0rhOF",
                "created": "2020-04-28T11:14:02.095",
                "name": "Countries",
                "shortName": "Countries",
                "dataDimensionType": "DISAGGREGATION",
                "dimensionType": "CATEGORY",
                "displayName": "Countries",
                "publicAccess": "rw------",
                "displayShortName": "Countries",
                "categoryCombos": [{"id": catcombo}],
                "categoryOptions": uid_catoption_list,
                "userGroupAccesses": [{"access": "rw------","userGroupUid": "UfhhwZK73Lg","displayName": "WIDP IT team","id": "UfhhwZK73Lg"}]
            })

        json.dump({"categories": new_category, "categoryCombos": new_cat_combo, "categoryOptions": new_catoptions}, outfile, indent=True, ensure_ascii=False)