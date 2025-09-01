import csv
import json
import os
import sys
from datetime import datetime
from os import listdir
from os.path import isfile, join

from DHIS2.cloner import dhis2api

output_dir = "output"
input_dir = "input"
levels = {
    36: "3",
    48: "4",
    60: "5",
    72: "6",
    84: "7",
    96: "8"
}


def main():
    global paths
    global uid_list
    is_csv = lambda fname: os.path.splitext(fname)[-1] in ['.csv']
    is_not_csv = lambda fname: not os.path.splitext(fname)[-1] in ['.csv']
    is_not_git = lambda fname: not fname.startswith(".git")
    applied_filter = is_not_git if is_csv else is_not_csv

    files = [f for f in filter(applied_filter, listdir(input_dir)) if isfile(join(input_dir, f))]
    for path_file in files:
        paths = dict()
        uid_list = list()
        load_data(path_file)
        print(paths)
        print(len(paths))

        cfg = get_config("config.json")
        user = cfg["user"]
        password = cfg["password"]
        server = cfg["server"]

        if not user or not password or not server:
            print("ERROR: Please provide server, username and password")
            sys.exit()

        api = dhis2api.Dhis2Api(server, user, password)

        feature_json_output = get_geojson_from_dhis(api, paths)

        with open(join(output_dir, path_file.replace(".csv", "") + '.geojson'), 'w') as outfile:
            json.dump(feature_json_output, outfile)


def assign_csv_data(row):
    level = levels.get(len(row[0]))
    path = row[0].split("/")

    parent = path[-2]

    if parent in paths.keys():
        add_level(level, parent, path[-1])
    else:
        paths[parent] = {"levels": list(), "ids": list()}
        add_level(level, parent, path[-1])


def add_level(level, parent, id):
    exist = False
    for item in paths[parent]["levels"]:
        if item == level:
            exist = True
    if not exist:
        paths[parent]["levels"].append(level)
    paths[parent]["ids"].append(id)


def load_data(path_file):
    with open(os.path.join("input", path_file)) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            assign_csv_data(row)


def get_geojson_from_dhis(api, paths):
    count = 0
    feature_json_output = {
        "type": "FeatureCollection",
        "features": list()
    }
    for parent in paths.keys():
        for level in paths[parent]["levels"]:
            count = count + 1
            print()
            dateTimeObj = datetime.now()
            print("api request " + str(count) + " time:" + str(dateTimeObj.hour), ':', str(dateTimeObj.minute), ':',
                  str(dateTimeObj.second), '.', str(dateTimeObj.microsecond))
            result = api.get("/organisationUnits.geojson?parent=" + parent + "&level=" + level)
            dateTimeObj = datetime.now()
            print("api response number " + str(count) + " time:" + str(dateTimeObj.hour), ':', str(dateTimeObj.minute),
                  ':', str(dateTimeObj.second), '.', str(dateTimeObj.microsecond))
            for item in result["features"]:
                if item["geometry"]["type"] != "Point":
                    del item['properties']
                    for id in paths[parent]["ids"]:
                        if item["id"] == id:
                            feature_json_output["features"].append(item)
    return feature_json_output


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
