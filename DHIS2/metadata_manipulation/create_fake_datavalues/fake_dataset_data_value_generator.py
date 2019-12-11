#!/usr/bin/env python3

"""
Data set data value fake generator
"""
import copy
import sys
import json
import argparse
import random

from cloner import dhis2api

output_skell = {"dataValues": []}


def main():

    global api

    args = get_args()

    cfg = get_config(args.config)
    output_preffix = cfg["config"]["output_prefix"]
    max_values = cfg["config"]["max_data_value_by_file"]
    default_coc = cfg["config"]["default_category_option_combo"]
    default_aoc = cfg["config"]["default_attribute_option_combo"]
    user = cfg["config"]["user"]
    password = cfg["config"]["password"]
    url = cfg["config"]["url"]
    rules = cfg["rules"]
    data_sets = cfg["datasets"]

    datavalues_limited_by_max = generate_data_values(max_values, default_coc, default_aoc, data_sets, rules)

    generate_json_files(datavalues_limited_by_max, output_preffix)

    if args.update:
        print ("Pushing values to dhis2 server")
        api = dhis2api.Dhis2Api(url, user, password)

        for data_values in datavalues_limited_by_max:
            for data in data_values["dataValues"]:
                query = get_query(data)
                response = api.post("/dataValues", params=query, payload=None, contenttype="text/html;charset=utf-8")

                print (response)
    print ("Done.")

def get_query(data):
    query = ("de=%s&co=%s&ds=%s&ou=%s&pe=%s&value=%s" % (data["dataElement"], data["categoryOptionCombo"], data["dataset_uid"], data["orgUnit"], data["period"],data["value"]))
    return query


def get_args():
    "Return arguments"
    parser = argparse.ArgumentParser(description=__doc__)
    add = parser.add_argument  # shortcut
    add('-c', '--config', default="config.json", help='file with configuration')
    add('-u', '--update', action='store_true', help='output a compacted json')
    return parser.parse_args()


def get_config(fname):
    "Return dict with the options read from configuration file"
    print('Reading from config file %s ...' % fname)
    try:
        with open(fname) as f:
            config = json.load(f)
    except (AssertionError, IOError, ValueError) as e:
        sys.exit('Error reading config file %s: %s' % (fname, e))
    return config


def convert_date(orig_date, date_format):
    from datetime import datetime
    orig_date = str(orig_date)
    d = datetime.strptime(orig_date, '%Y-%m-%d %H:%M:%S')
    d = d.strftime(date_format)
    return d


def get_dates(start_date, end_date, period_type):
    date_generated = generate_dates(end_date, start_date)
    return convert_dates_to_periods(date_generated, period_type)


def convert_dates_to_periods(date_generated, period_type):
    if period_type == "daily":
        date_format = "%Y%m%d"
    date_formatted = [convert_date(x, date_format) for x in date_generated]
    return date_formatted


def generate_dates(end_date, start_date):
    import datetime
    date_format = "%Y-%m-%d"
    start = datetime.datetime.strptime(start_date, date_format)
    end = datetime.datetime.strptime(end_date, date_format)
    date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days)]
    return date_generated


def get_value(rule, rules):
    for rule_action in rules:
        if rule_action["key"] == rule:
            return random.randint(int(rule_action["limit_down"]), int(rule_action["limit_up"]))
    print ("not rule detected for %s" %(rule))
    return 0


def generate_data_values(max_values, coc, aoc, data_sets, rules):
    count = 0
    data_values = list()
    data_values.append(copy.deepcopy(output_skell))
    for data_set in data_sets:
            dates = get_dates(data_set["start_date"], data_set["end_date"], data_set["period_type"])
            for date in dates:
                for org_unit in data_set["orgunits"]:
                    for data_element in data_set["data_elements"]:
                        data_value = get_data_value(aoc, coc, data_element, data_set["id"], date, org_unit, rules)
                        count = check_data_value_limit(count, data_values, max_values)
                        data_values[count]["dataValues"].append(data_value)

    return data_values


def get_data_value(aoc, coc, data_element, dataset, date, org_unit, rules):
    if "coc" in data_element.keys():
        coc = data_element["coc"]
    if "aoc" in data_element.keys():
        aoc = data_element["aoc"]
    data_value = (data_element["id"], date, org_unit["id"], coc, aoc, get_value(data_element["rule"], rules))
    data_value_formatted = ({"dataElement": data_value[0], "period": data_value[1],
                             "orgUnit": data_value[2], "categoryOptionCombo": data_value[3],
                             "attributeOptionCombo": data_value[4], "value": data_value[5], "dataset_uid": dataset})
    return data_value_formatted


def check_data_value_limit(count, data_values, max_values):
    if len(data_values[count]['dataValues']) == int(max_values):
        count = count + 1
        data_values.append(copy.deepcopy(output_skell))
    return count


def generate_json_files(datavalues_limited_by_max, output_preffix):
    count = 0
    for datavalues in datavalues_limited_by_max:
        count = count + 1
        file_name = output_preffix +"_"+ str(count) + ".json"
        with open(file_name, 'w') as outfile:
            json.dump(datavalues, outfile)
            print("Datavalues saved on file: "+file_name)

if __name__ == '__main__':
    main()
