#!/usr/bin/env python3

"""
Get a description of a program.
"""

# The functions here are useful too in an interactive session, because
# we can use all the objects retrieved with get_object() without
# having to make any new query.

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import dhis2 as d2
import json
import csv, json, sys

api_datasets_query = "dataSets?fields=[*]&paging=false&filter=id:in:[%s]"
api_indicators_query = "indicators?fields=[id,name,numerator,denominator,indicatorGroups]&paging=false"
api_indicator_groups = "indicatorGroups?fields=[*]&paging=false"


def main():
    args = get_args()

    d2.USER = args.user
    d2.URLBASE = args.urlbase
    dataset_query = ""
    for dataset in args.datasets:
        if dataset_query == "":
            dataset_query = dataset
        else:
            dataset_query = dataset_query +" ," + dataset
    url = api_datasets_query % dataset_query
    datasets = d2.get(url.replace(" ", ""))
    indicatorGroups = d2.get(api_indicator_groups)

    dataset_dataelements_list = list()
    for dataset in datasets["dataSets"]:
        for datasetelement in dataset["dataSetElements"]:
            dataset_dataelements_list.append(datasetelement["dataElement"]["id"])

    indicators = get_indicators(dataset_dataelements_list, indicatorGroups)

    with open(args.output, "w") as file:
        output = csv.writer(file)
        output.writerow(indicators[0].keys())
        for item in indicators:
            output.writerow(item.values())


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('datasets', nargs='*', help='id of the dataset used by the indicators')
    add('-o', '--output', help='output file')
    add('-u', '--user', metavar='USER:PASSWORD', required=True,
        help='username and password for server authentication')
    add('--urlbase', default='https://extranet-uat.who.int/dhis2',
        help='base url of the dhis server')
    return parser.parse_args()


def id_list(a):  # we often get lists like [{'id': 'xxxx'}, {'id': 'yyyy'}, ...]
    return [x['id'] for x in a]


def get_indicators(dataelement_list, indicatorGroups):
    indicators = list()
    all_indicators = d2.get(api_indicators_query)
    for indicator in all_indicators["indicators"]:
        get_indicator=False
        for uid in dataelement_list:
            if uid in indicator["denominator"] or uid in indicator["numerator"]:
                get_indicator=True
        if get_indicator:
            indicator["indicatorGroupsNames"] = list()
            for indicatorgroupuids in indicator["indicatorGroups"]:
                for indicatorGroup in indicatorGroups["indicatorGroups"]:
                    if indicatorgroupuids["id"] == indicatorGroup["id"]:
                        indicator["indicatorGroupsNames"].append(indicatorGroup["name"])

            indicators.append(indicator)

    return describe_indicators(indicators)


def describe_indicators(indicator):
    indicators = list()
    for x in indicator:
        indicators.append(describe_indicator(x))
    return indicators


def describe_indicator(indicator):
    try:
        name = indicator['name']
        numerator = "numerator: " + indicator['numerator']
        denominator = "denominator: " + indicator['denominator']
        indicatorGroups = indicator["indicatorGroupsNames"]
        id = indicator['id']

        return {"name":name, "id":id, "numerator":numerator, "denominator":denominator, "indicatorGroups":indicatorGroups}
    except KeyError:
        return '***%s***' % indicator  # could not find it


if __name__ == '__main__':
    main()
