
import json
import glob
import subprocess


files = glob.glob("/home/idelcano/temp/ESTools/DHIS2/metadata_manipulation/orgunit_formatter/uidfixer/ss/*.json")

def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return str(output).replace("b'", "").replace("\\n'", "")

for file in files:
    print (file)
    with open(file) as json_file:
        all_orgunits = json.load(json_file)
        new_list = list()
        for org_unit in all_orgunits["organisationUnits"]:
            if "id" in org_unit.keys():
                print("id detected")
                print (org_unit)
            else:
                org_unit["id"] = get_code()
            if org_unit["openingDate"] == "NAT00:00:00.000":
                print("nat detected")

    with open(file.replace("/ss/", "/ss_out/"), 'w') as outfile:
        json.dump(all_orgunits, outfile)