#! /usr/bin/env python
import os
import subprocess
import sys
import csv
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter as fmt
from datetime import datetime
from d2apy import dhis2api
import json

# subprocess.call('sudo node myscript.js', shell=True)

indicators_api_call = "/indicators.json?fields=id,name,shortName,numerator,denominator,filter,lastUpdatedBy[displayName],user[displayName],created,lastUpdated,userGroupAccesses,userAccess,publicAccess&paging=false"
update_datavalue = "/dataValues"
post_content = "de=%s&co=%s&ds=FnYgTt843G2&ou=H8RixfF8ugH&pe=%s&value=%s"


def get_indicators(api):
    return api.get(indicators_api_call)


def match_wrong_expressions(indicators, api, method):
    indicators_with_wrong_expresions = {"indicators": []}
    for indicator in indicators["indicators"]:
        if method == "api":
            error = get_indicators_with_errors(api, indicator, indicators_with_wrong_expresions)
            if error:
                time.sleep(10)
                error = get_indicators_with_errors(api, indicator, indicators_with_wrong_expresions)
                if error:
                    print("Error in second attempt with the indicator" + indicator["id"])
        if method == "node":
            print("not supported at this moment")
            # Call node js
    return indicators_with_wrong_expresions


def get_indicators_with_errors(api, indicator, indicators_with_wrong_expresions):
    try:
        apirequests(api, indicator, indicators_with_wrong_expresions)
        return False
    except:
        print("Error with the indicator" + indicator["id"])
        return True


def apirequests(api, indicator, indicators_with_wrong_expresions):
    expression_errors = False
    time.sleep(0.1)
    numerator_result = api.post("/indicators/expression/description", payload=indicator["numerator"],
                                contenttype='text/plain')
    time.sleep(0.1)
    denominator_result = api.post("/indicators/expression/description", payload=indicator["denominator"],
                                  contenttype='text/plain')
    time.sleep(0.1)
    if filter in indicator.keys():
        filter_result = api.post("/indicators/expression/description", payload=indicator["filter"],
                                 contenttype='text/plain')
        if filter_result["message"] != "Valid":
            expression_errors = True
            indicator["filter_error"] = denominator_result["message"]
    if numerator_result["message"] != "Valid":
        expression_errors = True
        indicator["numerator_error"] = numerator_result["message"]
    if denominator_result["message"] != "Valid":
        expression_errors = True
        indicator["denominator_error"] = denominator_result["message"]
    if expression_errors:
        indicators_with_wrong_expresions["indicators"].append(indicator)
    return indicator


def report_count_of_invalid_indicators(indicators, url, user, password, data_element_uid, category_option_combo_uid,
                                       period):
    api_destine_server = dhis2api.Dhis2Api(url, user, password)
    query = post_content % (data_element_uid, category_option_combo_uid, period, indicators)
    return api_destine_server.post(update_datavalue, params=query, payload="", contenttype='text/plain')


def create_report(indicators, report_name, period, output_folder, csv_id):
    name = 'indicators_report_' + report_name + '_' + period + '.csv'
    filename = os.path.join(output_folder, name)
    with open(filename, mode='w') as report_file:
        report_file_writer = csv.writer(report_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        report_file_writer.writerow(
            ['uid', 'name', 'shortName', 'numerator', 'denominator', 'filter', 'user', 'lastUpdatedBy', 'created',
             'lastUpdated', 'userGroupAccesses', 'userAccess', 'publicAccess', 'nominator_error', 'denominator_error',
             'filter_error'])
        for indicator in indicators["indicators"]:
            try:
                user = indicator["user"]["displayName"]
                lastUpdatedBy = ""
                if "lastUpdatedBy" in indicator.keys() and "displayName" in indicator["lastUpdatedBy"].keys():
                    lastUpdatedBy = indicator["lastUpdatedBy"]["displayName"]
                userAccess = "-"
                if "userAccess" in indicator.keys():
                    userAccess = indicator["userAccess"]
                userGroupAccesses = "-"
                if "userGroupAccesses" in indicator.keys():
                    userGroupAccesses = indicator["userGroupAccesses"]
                filter = "-"
                if "filter" in indicator.keys():
                    filter = indicator["filter"]
                numerator_error = "-"
                if "numerator_error" in indicator.keys():
                    numerator_error = indicator["numerator_error"]
                denominator_error = "-"
                if "denominator_error" in indicator.keys():
                    denominator_error = indicator["denominator_error"]
                filter_error = "-"
                if "filter_error" in indicator.keys():
                    filter_error = indicator["filter_error"]
                report_file_writer.writerow(
                    [indicator["id"], indicator["name"], indicator["shortName"], indicator["numerator"],
                     indicator["denominator"], filter, user, lastUpdatedBy, indicator["created"], indicator["lastUpdated"],
                     userGroupAccesses, userAccess,
                     indicator["publicAccess"], numerator_error, denominator_error, filter_error])
            except:
                print("error creating report for the  indicator: " + indicator["id"])

    import gspread

    gc = gspread.service_account()

    content = open(filename, 'r').read()
    gc.import_csv(csv_id, content)


def main():
    args = get_args()
    cfg = get_config(args.config)
    servers = cfg["servers"]
    period = datetime.today().strftime('%Y%m%d')
    for server in servers:
        api_origin = dhis2api.Dhis2Api(server["origin"]["server"], server["origin"]["user"], server["origin"]["password"])
        indicators = get_indicators(api_origin)
        print("Server:" + server["origin"]["server"])
        indicators = match_wrong_expressions(indicators, api_origin, server["method"])
        create_report(indicators, server["report_name"], period, args.output, server["destine"]["id"])
        report_count_of_invalid_indicators(len(indicators['indicators']), server["destine"]["server"],
                                           server["destine"]["user"], server["destine"]["password"],
                                           server["destine"]["dataelement_uid"],
                                           server["destine"]["categoryoptioncombo_uid"], period)


def get_config(fname):
    "Return dict with the options read from configuration file"
    print('Reading from config file %s ...' % fname)
    try:
        with open(fname) as f:
            config = json.load(f)
    except (AssertionError, IOError, ValueError) as e:
        sys.exit('Error reading config file %s: %s' % (fname, e))
    return config


def get_args():
    "Parse command-line arguments and return them"
    global sort_fields
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut

    add('-c', '--config', help='config file (absolute path)', required=True)
    add('-o', '--output', help='output folder (absolute path)', required=True)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
