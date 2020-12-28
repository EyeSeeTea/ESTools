import csv
import json
import os
import sys
from datetime import time
from enum import Enum
from os import listdir
from os.path import isfile, join

from DHIS2.cloner import dhis2api

input_dir = "input"
output_dir = "output"
config_file = "config.json"
query_programs = "/metadata.json?filter=id:in:[%s]&paging=false"
query_orgunit_levels = "/organisationUnits.json?filter=path:like:%s/&filter=level:eq:%d&fields=id&paging=false"
query_orgunit = "/organisationUnits/%s.json?fields=id&paging=false"
query_orgunit_children = "/organisationUnits/%s.json?fields=children&paging=false"
query_orgunit_descendants = "/organisationUnits/%s.json?includeDescendants=true&fields=id&paging=false"
query_orgunitgroups = "/organisationUnitGroups/%s.json?fields=id&paging=false"


class Children(Enum):
    no = 1
    yes = 2
    level = 3
    alldescendants = 4
    orgunitgroup = 5


def assign_fields(ou, dataset, eventprogram, trackerprogram, children, replace, data):
    if ou is None:
        print("Ou field is required")
        sys.exit()
    if children is None:
        print("With children field is required")
        sys.exit()

    if not dataset and not eventprogram and not trackerprogram :
        print("At least one dataset, event program, or tracker program is required")
        sys.exit()
    if dataset:
        data["dataSets"].append(dataset)
        identifier = dataset
    if eventprogram:
        data["programs"].append(eventprogram)
        identifier = eventprogram
    if trackerprogram:
        data["programs"].append(trackerprogram)
        identifier = trackerprogram

    if replace is None or replace.lower() == "no":
        replace = False
    elif replace.lower() == "yes":
        replace = True
    else:
        print("replace field is not valid (Yes / No )")
        sys.exit()
    data["items"].append({"identifier": identifier, "children": children, "orgUnit": ou, "replace": replace, "query": ""})


def get_data_from_csv(files):
    data = {"programs": [], "dataSets": [], "items": []}
    for path_file in files:
        with open(path_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    line_count += 1
                    ou = row[0]
                    children = row[1].lower()
                    dataset = row[2]
                    eventprogram = row[3]
                    trackerprogram = row[4]
                    replace = row[5]
                    assign_fields(ou, dataset, eventprogram, trackerprogram, children, replace, data)
            return data


def generate_queries(data):
    for item in data["items"]:
        children = item["children"]
        org_unit_uid = item["orgUnit"]
        if Children.no.name == children:
            query = query_orgunit % (item["orgUnit"])
        elif Children.level.name in children:
            import re
            level = re.findall(r'\d+', children)
            query = query_orgunit_children % (org_unit_uid, level)
        elif Children.yes.name == children:
            query = query_orgunit_children % org_unit_uid
        elif Children.alldescendants.name == children:
            query = query_orgunit_descendants % org_unit_uid
        elif Children.orgunitgroup.name == children:
            query = query_orgunitgroups % org_unit_uid
        item["query"] = query


def append_org_units(programs_from_server, data):
    for item in data:
        append_in_metadata(item, programs_from_server, "programs")
        append_in_metadata(item, programs_from_server, "dataSets")


def append_in_metadata(item, programs_from_server, key):
    for metadata_item in programs_from_server[key]:
        if item["identifier"] == metadata_item["id"]:
            if item["replace"]:
                metadata_item["organisationUnits"] = item["organisationUnits"]
            else:
                item_orgunits = set(item["organisationUnits"])
                program_orgunits = set(metadata_item["organisationUnits"])
                new_orgunits = list(item_orgunits - program_orgunits)
                metadata_item["organisationUnits"] = program_orgunits + new_orgunits


def execute_queries(api, data):
    for item in data:
        children = item["children"]
        query = item["query"]
        orgunits = api.get(query)
        #sleep some seconds between api calls
        time.sleep(3)

        if Children.no == children:
            item["organisationUnits"] = {"id": orgunits["id"]}
        elif Children.yes.name == children:
            item["organisationUnits"] = orgunits["children"]
        elif Children.level.name == children or Children.alldescendants.name == children:
            item["organisationUnits"] = orgunits["organisationUnits"]
        elif Children.orgunitgroup.name == children:
            for orgunitgroup in orgunits["organisationUnitGroup"]:
                item["organisationUnits"] = orgunitgroup["organisationUnits"]



def main():
    global paths
    global uid_list
    global input_data
    input_data = dict()
    path = os.path.abspath(__file__)
    applied_filter = lambda fname: fname.endswith('.csv')
    if "/" in path:
        path = path[:path.rfind('/')+1]
    elif "\\" in path:
        path = path[:path.rfind('\\') + 1]
    fixed_input_dir = join(path, input_dir)
    fixed_output_dir = join(path, output_dir)
    files = [join(fixed_input_dir, f) for f in filter(applied_filter, listdir(fixed_input_dir)) if isfile(join(fixed_input_dir, f))]
    cfg = get_config(join(path,config_file))
    user = cfg["user"]
    password = cfg["password"]
    server = cfg["server"]

    if not user or not password or not server:
        print("ERROR: Please provide server, username and password")
        sys.exit()
    input_data = get_data_from_csv(files)

    api = dhis2api.Dhis2Api(server, user, password)

    programs_from_server = get_programs_from_server(api, input_data)
    generate_queries(input_data)
    execute_queries(api, input_data)
    append_org_units(programs_from_server, input_data)
    write_to_json(fixed_output_dir, programs_from_server)


def get_programs_from_server(api, data):
    program_uids = ""
    for dataset in data["dataSets"]:
        program_uids = program_uids + dataset + ","
    for program in data["programs"]:
        program_uids = program_uids + program + ","
    program_uids = program_uids[:program_uids.rfind(',')]
    return api.get(query_programs % (program_uids))


def write_to_json(file, content):
    from datetime import datetime
    with open(join(file + "importer_"+ datetime.now() + ".json"), 'w', encoding='utf-8') as file:
        json.dump(content, file, indent=4)


def get_config(fname):
    "Return dict with the options read from configuration file"
    print('Reading from config file %s ...' % fname)
    try:
        with open(fname) as f:
            config = json.load(f)
    except (AssertionError, IOError, ValueError) as e:
        sys.exit('Error reading config file %s: %s' % (fname, e))
    return config


if __name__ == '__main__':
    main()
