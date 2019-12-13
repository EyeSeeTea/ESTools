#!/usr/bin/env python3

"""
Data set data value fake generator
"""
import copy
import sys
import json
import argparse
import random
import numpy as np, numpy.random

from DHIS2.cloner import dhis2api

output_skell = {"dataValues": []}

rand_limits = "rand_limits"
rand_total = "rand_total"
coc_percentage_yearly = "coc_percentage_yearly"
rand_percent = "rand_percent"
malaria_cases = "malaria_cases"

daily ="daily"
yearly = "yearly"
monthly = "monthly"
active_total = dict()


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
    date_generated = generate_dates(end_date, start_date, period_type)
    date_and_period = convert_dates_to_periods(date_generated, period_type)

    return date_and_period


def convert_dates_to_periods(date_generated, period_type):
    if period_type == daily:
        date_format = "%Y%m%d"
    elif period_type == monthly:
        date_format = "%Y-%m"
    elif period_type == yearly:
        date_format = "%Y"

    date_formatted = [{"date": x, "period": convert_date(x, date_format)} for x in date_generated]
    return date_formatted


def generate_dates(end_date, start_date, period_type):
    import datetime
    date_format = "%Y-%m-%d"

    start = datetime.datetime.strptime(start_date, date_format)
    end = datetime.datetime.strptime(end_date, date_format)

    if period_type == daily:
        return [start + datetime.timedelta(days=x) for x in range(0, (end - start).days)]

    elif period_type == monthly:
        date_and_period = get_monthly_periods(end, start)
        return date_and_period

    elif period_type == yearly:
        start_year = start.year
        end_year = end.year
        return [datetime.datetime(x, 1, 1) for x in range(start_year, end_year+1)]


def get_monthly_periods(end, start):
    import datetime
    days = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days)]
    periods = dict()
    for day in days:
        key_month = get_month_with_zero_values(day)
        key = str(day.year) + key_month
        if key not in periods.keys():
            periods[key] = day
    date_and_period = dict()
    for period_key in periods.keys():
        if periods[period_key].day == 1:
            date_and_period[periods[period_key]] = period_key
    return date_and_period


def get_month_with_zero_values(month):
    key_month = str(month)
    if len(key_month) == 1:
        key_month = "0" + key_month
    return key_month


def get_days(date_value):
    from datetime import date
    print (date_value.month)
    if date_value.month == 12:
        return 31
    return (date(date_value.year, date_value.month+1, 1) - date(date_value.year, date_value.month, 1)).days


def get_value(dataset, dataelement, rules, date):
    global active_total
    rule = dataelement["rule"]
    for rule_action in rules:
        item_key = dataset + "-" + dataelement["id"] + "-" + dataelement["orgUnit"] + "-" + dataelement["coc"] +"-" + rule
        date_key = item_key + get_date_key(date.year, date.month, date.day)
        if rule in rule_action.keys():
            if rule_action[rule]["type"] == malaria_cases:
                limit_down = rule_action[rule]["limit_down"]
                limit_up = rule_action[rule]["limit_up"]
                value = random.randint(int(limit_down), int(limit_up))
                for rule_item in rule_action[rule]["items"]:
                    if rule_item["increase_month"] == get_month_with_zero_values(date.month):
                        limit_down = rule_item["limit_down"]
                        limit_up = rule_item["limit_up"]
                        extra_value = random.randint(int(limit_down), int(limit_up))
                        value = value + extra_value

                active_total[item_key + get_date_key(date.year, date.month, "01")] = int(value)
                return active_total[date_key]

            elif rule_action[rule]["type"] == rand_total:
                for rule_item in rule_action[rule]["items"]:
                    if int(rule_item["month"]) == date.month:
                        if date_key not in active_total.keys():
                            get_total_randomized_by_month_days(date, rule_item, item_key)
                        return active_total[date_key]

            elif rule_action[rule]["type"] == rand_limits:
                for rule_item in rule_action[rule]["items"]:
                    if int(rule_item["month"]) == date.month:
                        if date_key not in active_total.keys():
                            get_total_randomized_with_limits(date, rule_item, item_key)
                        return active_total[date_key]

            elif rule_action[rule]["type"] == coc_percentage_yearly:
                items = rule_action[rule]["items"]
                years = rule_action[rule]["years"]
                total = years[str(date.year)]
                for rule_item in items:
                    if dataelement["coc"] == rule_item["coc"]:
                        get_percentage(date, item_key, rule_item["percentage"], total)
                        return active_total[date_key]

            elif rule_action[rule]["type"] == rand_percent:
                limit_up = int(rule_action[rule]["limit_up"])
                limit_down = int(rule_action[rule]["limit_down"])
                random_percentage = random.randint(limit_down, limit_up)
                years = rule_action[rule]["years"]
                total = years[str(date.year)]
                get_percentage(date, item_key, random_percentage, total)
                return active_total[date_key]

    print ("not rule detected for %s" %(rule))
    return 0


def get_date_key(year, month, day):
    return str(year) + "-" + get_month_with_zero_values(str(month)) + "-" + get_month_with_zero_values(
        str(day))


def get_percentage(date, item_key, percentage, total):
    value = round(int(float(total) * float(percentage)) / 100)

    active_total[item_key + get_date_key(date.year, date.month, date.day)] = int(value)
    return active_total


def get_total_randomized_by_month_days(date, rule_item, item_key):
    global active_total
    size = get_days(date)
    array1 = np.random.dirichlet(np.ones(size), size=int(rule_item["total"]))
    total_0_axis = np.sum(array1, axis=0, dtype=float)
    listed = np.array(total_0_axis).tolist()
    day = 1
    for item in listed:
        active_total[item_key + get_date_key(date.year, date.month, day)] = (round(item, 2))
        day = day + 1
    return active_total


def get_total_randomized_with_limits(date, rule_item, item_key):
    global active_total

    size = get_days(date)
    active_total[item_key + get_date_key(date.year, date.month, date.day)] \
        = (round(random.uniform(float(rule_item["limit_down"]), float(rule_item["limit_up"])), 2))
    rand_day = random.randint(1, size)
    other_rand = random.randint(1, size)
    while other_rand == rand_day:
        other_rand = random.randint(1, size)
    active_total[item_key + get_date_key(date.year, date.month, rand_day)] = rule_item["limit_down"]
    active_total[item_key + get_date_key(date.year, date.month, other_rand)] = rule_item["limit_up"]

    return active_total


def generate_data_values(max_values, coc, aoc, data_sets, rules):
    count = 0
    data_values = list()
    data_values.append(copy.deepcopy(output_skell))
    for data_set in data_sets:
            date_and_periods = get_dates(data_set["start_date"], data_set["end_date"], data_set["period_type"])
            for date_and_period in date_and_periods:
                for org_unit in data_set["orgunits"]:
                    for data_element in data_set["data_elements"]:
                        if "coc" in data_element.keys():
                            coc = data_element["coc"]
                        else:
                            data_element["coc"] = coc
                        if "aoc" in data_element.keys():
                            aoc = data_element["aoc"]
                        else:
                            data_element["aoc"] = aoc
                        data_element["orgUnit"] = org_unit["id"]
                        data_value = get_data_value(data_element, data_set["id"], date_and_period, rules)
                        count = check_data_value_limit(count, data_values, max_values)
                        data_values[count]["dataValues"].append(data_value)
                print (active_total)

    return data_values


def get_data_value(data_element, dataset, date_and_period, rules):
    value = get_value(dataset, data_element, rules, date_and_period["date"])
    data_value_formatted = ({"dataElement": data_element["id"], "period": date_and_period["period"],
                             "orgUnit": data_element["orgUnit"], "categoryOptionCombo": data_element["coc"],
                             "attributeOptionCombo": data_element["aoc"], "value": value, "dataset_uid": dataset})
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