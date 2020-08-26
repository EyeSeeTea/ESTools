import json
import os
import subprocess
import json
import csv
import sys
from os import listdir
from os.path import isfile, join

from ESTools.DHIS2.metadata_manipulation.malcsv2dhis import dhis2api

orgunit_list = list()
output_dir = "output"
input_dir = "input"


def get_config(fname):
    "Return dict with the options read from configuration file"
    print('Reading from config file %s ...' % fname)
    try:
        with open(fname) as f:
            config = json.load(f)
    except (AssertionError, IOError, ValueError) as e:
        sys.exit('Error reading config file %s: %s' % (fname, e))
    return config


def main():
    cfg = get_config("config.json")
    user = cfg["user"]
    password = cfg["password"]
    server = cfg["server"]
    programs = cfg["programs"]
    orgunitgroups = cfg["organisationUnitGroups"]
    list_of_programs = {"programs":[]}
    list_of_orgunitgroups = {"organisationUnitGroups":[]}
    api = dhis2api.Dhis2Api(server, user, password)
    for program in programs:
        query = "/29/programs/%s.json" % (
            program)
        data = api.get(query)
        list_of_programs["programs"].append(data)
        for program in list_of_programs["programs"]:
            program.pop("translations", None)
    for orgunitgroup in orgunitgroups:
        query = "/29/organisationUnitGroups/%s.json" % (
            orgunitgroup)
        data = api.get(query)
        list_of_orgunitgroups["organisationUnitGroups"].append(data)
        for orgunit in list_of_orgunitgroups["organisationUnitGroups"]:
            orgunit.pop("translations", None)
            orgunit.pop("attributeValues", None)


    is_csv = lambda fname: os.path.splitext(fname)[-1] in ['.json']
    is_not_csv = lambda fname: not os.path.splitext(fname)[-1] in ['.json']
    is_not_git = lambda fname: not fname.startswith(".git")
    applied_filter = is_not_git if is_csv else is_not_csv

    files = [f for f in filter(applied_filter, listdir(input_dir)) if isfile(join(input_dir, f))]
    for path_file in files:
        with open(os.path.join("input", path_file), encoding='utf-8') as json_file:
            data = json.load(json_file)
            for organisationUnit in data["organisationUnits"]:
                for program in list_of_programs["programs"]:
                    program["organisationUnits"].append({"id": organisationUnit["id"]})

                for orgunitgroup in list_of_orgunitgroups["organisationUnitGroups"]:
                    orgunitgroup["organisationUnits"].append({"id": organisationUnit["id"]})

        #check diff
        for program in list_of_programs["programs"]:
            for orgunitgroup in list_of_orgunitgroups["organisationUnitGroups"]:
                for program_orgunit in program["organisationUnits"]:
                    if program_orgunit not in orgunitgroup["organisationUnits"]:
                        print (program_orgunit["id"] + " not exist in orgunitgroup")

        for orgunitgroup in list_of_orgunitgroups["organisationUnitGroups"]:
            for program in list_of_programs["programs"]:
                for orgunitgroup_orgunit in orgunitgroup["organisationUnits"]:
                    if orgunitgroup_orgunit not in program["organisationUnits"]:
                        print (orgunitgroup_orgunit["id"] + " not exist in program")

        with open(join(output_dir, path_file + '_programs.json'), 'w', encoding="utf-8") as outfile:
            json.dump(list_of_programs, outfile, ensure_ascii=False)
        with open(join(output_dir, path_file + '_orgunitgroups.json'), 'w', encoding="utf-8") as outfile:
            json.dump(list_of_orgunitgroups, outfile, ensure_ascii=False)


if __name__ == '__main__':
    main()
