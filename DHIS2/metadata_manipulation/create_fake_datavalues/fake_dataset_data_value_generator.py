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

#rules
rand_limits = "rand_limits"
rand_total = "rand_total"
coc_percentage_yearly = "coc_percentage_yearly"
rand_percent = "rand_percent"
rand_increase_by_month = "rand_increase_by_month"
referenced_percentage = "referenced_percentage"
referenced_percentage_by_sex = "referenced_percentage_by_sex"
referenced_sum = "referenced_sum"
referenced_sum_with_random_limits = "referenced_sum_with_random_limits"
referenced_with_random_limits = "referenced_with_random_limits"

#periods
daily ="daily"
yearly = "yearly"
monthly = "monthly"

#global key of values
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
    if date_value.month == 12:
        return 31
    return (date(date_value.year, date_value.month+1, 1) - date(date_value.year, date_value.month, 1)).days


def get_item_key(dataset_id, dataelemet_id, orgunit_id, coc_id, rule):
    return dataset_id + "-" + dataelemet_id + "-" + orgunit_id + "-" + coc_id + "-" + rule


def get_value(dataset, dataelement, rules, date):
    global active_total
    rule_key = dataelement["rule"]
    for rule_action in rules:
        if rule_action["rule_key"] != rule_key:
            continue
        item_key = get_item_key(dataset, dataelement["id"], dataelement["orgUnit"], dataelement["coc"], rule_key)
        date_key = item_key + get_date_key(date.year, date.month, date.day)

        if rule_action["type"] == referenced_with_random_limits:
            # sum two values and increase using random limits.
            return calculate_referenced_sum_with_random_limit_increase(active_total, dataelement, dataset, date, date_key,
                                                                           rule_key, rule_action)
        elif rule_action["type"] == referenced_sum_with_random_limits:
            # sum two values and increase using random limits.
            return calculate_all_cases_adminsion_increase_rule(active_total, dataelement, dataset, date, date_key,
                                                                   rule_key, rule_action)

        elif rule_action["type"] == referenced_sum:
            # sum two existing values
            return calculate_referenced_sum_rule(active_total, dataelement, dataset, date, date_key, rule_key,
                                                     rule_action)

        elif rule_action["type"] == rand_increase_by_month:
            # generate random number with default random limits or month random increase based on limits
            return calculate_malaria_cases_admissions(active_total, date, date_key, item_key, rule_action)

        elif rule_action["type"] == referenced_percentage_by_sex:
            # percentage of existing reference spited by sex
            return calculate_referenced_percentage_by_sex(active_total, dataelement, dataset, date, date_key, item_key,
                                                           rule_key, rule_action)
        elif rule_action["type"] == referenced_percentage:
            # percentage of existing reference
            return calculate_referenced_percentage_rule(active_total, dataelement, dataset, date, date_key, item_key,
                                                            rule_key, rule_action)
        elif rule_action["type"] == rand_total:
            # rand based on total number by month
            return calculate_rand_total_rule(active_total, date, date_key, item_key, rule_key, rule_action)

        elif rule_action["type"] == rand_limits:
            # rand based on limits numbers by month
            return calculate_rand_limits_rule(active_total, date, date_key, item_key, rule_key, rule_action)

        elif rule_action["type"] == coc_percentage_yearly:
            # calculate given percentage from given totals by year for yearly periods
            return calculate_coc_percentage_yearly_rule(active_total, dataelement, date, date_key, item_key, rule_key,
                                                            rule_action)

        elif rule_action["type"] == rand_percent:
            return calculate_rand_percent_rule(active_total, date, date_key, item_key, rule_key, rule_action)
        else:
            print (rule_action["type"] + "not found")

    print ("not rule detected for %s" %(rule_key))
    return 0


def calculate_rand_total_rule(active_total, date, date_key, item_key, rule, rule_action):
    for rule_item in rule_action["items"]:
        if int(rule_item["month"]) == date.month:
            if date_key not in active_total.keys():
                get_total_randomized_by_month_days(date, rule_item, item_key)
    return active_total[date_key]


def calculate_rand_limits_rule(active_total, date, date_key, item_key, rule, rule_action):
    for rule_item in rule_action["items"]:
        if int(rule_item["month"]) == date.month:
            if date_key not in active_total.keys():
                get_total_randomized_with_limits(date, rule_item, item_key)
    return active_total[date_key]


def calculate_coc_percentage_yearly_rule(active_total, dataelement, date, date_key, item_key, rule, rule_action):
    items = rule_action["items"]
    years = rule_action["years"]
    total = years[str(date.year)]
    for rule_item in items:
        if dataelement["coc"] == rule_item["coc"]:
            get_percentage(date, item_key, rule_item["percentage"], total)
    return active_total[date_key]


def calculate_rand_percent_rule(active_total, date, date_key, item_key, rule, rule_action):
    # rand percentage based on total with limits for yearly periods
    limit_up = int(rule_action["limit_up"])
    limit_down = int(rule_action["limit_down"])
    random_percentage = random.randint(limit_down, limit_up)
    years = rule_action["years"]
    total = years[str(date.year)]
    get_percentage(date, item_key, random_percentage, total)
    return active_total[date_key]


def calculate_referenced_percentage_by_sex(active_total, dataelement, dataset, date, date_key, item_key, rule,
                                           rule_action):
    percentage = rule_action["percentage"]
    sex_percentage = ""
    referenced_data_element = ""
    referenced_coc = ""
    referenced_key = ""
    for item in rule_action["items"]:
        if item["active_data_element"] == dataelement["id"]:
            if item["male_coc"] == dataelement["coc"]:
                referenced_data_element = item["referenced_uid"]
                sex_percentage = item["male_percent"]
            if item["female_coc"] == dataelement["coc"]:
                referenced_data_element = item["referenced_uid"]
                sex_percentage = item["female_percent"]
            if referenced_data_element != "":
                referenced_coc = item["referenced_coc"]
                referenced_key = item["referenced_key"]
    if referenced_coc == "" or referenced_data_element == "":
        print("referenced not found for:" + dataelement["id"] + " coc: " + dataelement["coc"] + "" + rule)
        return 0
    else:
        referenced_item_key = get_item_key(dataset, referenced_data_element, dataelement["orgUnit"], referenced_coc, referenced_key)
        referenced_complete_key = referenced_item_key + get_date_key(date.year, date.month, "01")
        referenced_value = active_total[referenced_complete_key]
        value = round(int(float(referenced_value) * float(percentage)) / 100)
        value = round(int(float(value) * float(sex_percentage)) / 100)
        active_total[item_key + get_date_key(date.year, date.month, date.day)] = int(value)
        return active_total[date_key]


def calculate_referenced_percentage_rule(active_total, dataelement, dataset, date, date_key, item_key, rule,
                                         rule_action):
    percentage = rule_action["percentage"]
    referenced_data_element = ""
    referenced_coc = ""
    referenced_key = ""
    for item in rule_action["items"]:
        if item["active_data_element"] == dataelement["id"]:
            if item["active_coc"] == dataelement["coc"]:
                referenced_data_element = item["referenced_uid"]
                referenced_coc = item["referenced_coc"]
                referenced_key = item["referenced_key"]
    if referenced_coc == "" or referenced_data_element == "":
        print("referenced not found for:" + dataelement["id"] + " coc: " + dataelement["coc"])
        return 0
    else:
        referenced_item_key = \
            get_item_key(dataset, referenced_data_element, dataelement["orgUnit"], referenced_coc, referenced_key)
        referenced_value = active_total[referenced_item_key + get_date_key(date.year, date.month, "01")]
    get_percentage(date, item_key, percentage, referenced_value)
    return active_total[date_key]


def calculate_malaria_cases_admissions(active_total, date, date_key, item_key, rule_action):
    limit_down = rule_action["limit_down"]
    limit_up = rule_action["limit_up"]
    value = random.randint(int(limit_down), int(limit_up))
    for rule_item in rule_action["items"]:
        if rule_item["increase_month"] == get_month_with_zero_values(date.month):
            limit_down = rule_item["limit_down"]
            limit_up = rule_item["limit_up"]
            extra_value = random.randint(int(limit_down), int(limit_up))
            value = value + extra_value
    active_total[item_key + get_date_key(date.year, date.month, "01")] = int(value)
    return active_total[date_key]


def calculate_referenced_sum_rule(active_total, dataelement, dataset, date, date_key, rule, rule_action):
    referenced_data_element = ['0', '0']
    referenced_coc = ['0', '0']
    referenced_key = ['0', '0']
    referenced_value = ['0', '0']
    for item in rule_action["items"]:
        if item["active_data_element"] == dataelement["id"]:
            if item["active_coc"] == dataelement["coc"]:
                referenced_data_element[0] = item["referenced_uid"]
                referenced_coc[0] = item["referenced_coc"]
                referenced_key[0] = item["referenced_key"]
                referenced_data_element[1] = item["referenced_uid2"]
                referenced_coc[1] = item["referenced_coc2"]
                referenced_key[1] = item["referenced_key2"]
    if referenced_coc[0] == "0" or referenced_data_element[0] == "0":
        print("referenced not found for:" + dataelement["id"] + " coc: " + dataelement["coc"])
        return 0
    else:
        referenced_item_key = \
            get_item_key(dataset, referenced_data_element[0], dataelement["orgUnit"], referenced_coc[0],
                         referenced_key[0])
        referenced_value[0] = active_total[referenced_item_key + get_date_key(date.year, date.month, "01")]
        referenced_item_key = \
            get_item_key(dataset, referenced_data_element[1], dataelement["orgUnit"], referenced_coc[1],
                         referenced_key[1])
        referenced_value[1] = active_total[referenced_item_key + get_date_key(date.year, date.month, "01")]
    active_total[date_key] = referenced_value[0] + referenced_value[1]
    return active_total[date_key]

def calculate_referenced_sum_with_random_limit_increase(active_total, dataelement, dataset, date, date_key, rule, rule_action):
    limit_up = rule_action["limit_up"]
    limit_down = rule_action["limit_down"]
    referenced_data_element = ""
    referenced_coc = ""
    referenced_key = ""
    for item in rule_action["items"]:
        if item["active_data_element"] == dataelement["id"]:
            if item["active_coc"] == dataelement["coc"]:
                referenced_data_element = item["referenced_uid"]
                referenced_coc = item["referenced_coc"]
                referenced_key = item["referenced_key"]
    if referenced_coc == "" or referenced_data_element == "":
        print("referenced not found for:" + dataelement["id"] + " coc: " + dataelement["coc"])
        return 0
    else:
        referenced_item_key = \
            get_item_key(dataset, referenced_data_element, dataelement["orgUnit"], referenced_coc,
                         referenced_key)
        referenced_value = active_total[referenced_item_key + get_date_key(date.year, date.month, "01")]
    active_total[date_key] = referenced_value + (
        random.randint(int(limit_down), int(limit_up)))
    return active_total[date_key]


def calculate_all_cases_adminsion_increase_rule(active_total, dataelement, dataset, date, date_key, rule, rule_action):
    limit_up = rule_action["limit_up"]
    limit_down = rule_action["limit_down"]
    referenced_data_element = ['0', '0']
    referenced_coc = ['0', '0']
    referenced_key = ['0', '0']
    referenced_value = ['0', '0']
    for item in rule_action["items"]:
        if item["active_data_element"] == dataelement["id"]:
            if item["active_coc"] == dataelement["coc"]:
                referenced_data_element[0] = item["referenced_uid"]
                referenced_coc[0] = item["referenced_coc"]
                referenced_key[0] = item["referenced_key"]
                referenced_data_element[1] = item["referenced_uid2"]
                referenced_coc[1] = item["referenced_coc2"]
                referenced_key[1] = item["referenced_key2"]
    if referenced_coc[0] == "0" or referenced_data_element[0] == "0":
        print("referenced not found for:" + dataelement["id"] + " coc: " + dataelement["coc"])
        return 0
    else:
        referenced_item_key = \
            get_item_key(dataset, referenced_data_element[0], dataelement["orgUnit"], referenced_coc[0],
                         referenced_key[0])
        referenced_value[0] = active_total[referenced_item_key + get_date_key(date.year, date.month, "01")]
        referenced_item_key = \
            get_item_key(dataset, referenced_data_element[1], dataelement["orgUnit"], referenced_coc[1],
                         referenced_key[1])
        referenced_value[1] = active_total[referenced_item_key + get_date_key(date.year, date.month, "01")]
    active_total[date_key] = referenced_value[0] + referenced_value[1] + (
        random.randint(int(limit_down), int(limit_up)))
    return active_total[date_key]


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
            #print (active_total)

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
