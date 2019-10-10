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
api_simple_indicators_query = "indicators?fields=[id,name,numerator,denominator,indicatorGroups]&paging=false"
api_indicators_query = "indicators?fields=[*]&paging=false"
api_indicator_groups = "indicatorGroups?fields=[*]&paging=false"


def main():
    args = get_args()

    d2.USER = args.user
    d2.URLBASE = args.urlbase
    dataset_query = ""
    datasets = get_datasets(args, dataset_query)

    dataset_dataelements_list = list()
    for dataset in datasets["dataSets"]:
        for datasetelement in dataset["dataSetElements"]:
            dataset_dataelements_list.append(datasetelement["dataElement"]["id"])

    if args.indicatorGroups:
        indicatorGroups = d2.get(api_indicator_groups)
        indicators = get_simplified_indicators(dataset_dataelements_list, indicatorGroups)
    else:
        indicators = get_indicators(dataset_dataelements_list)

    output = json.dumps({"indicators": indicators}, indent=4, sort_keys=True)
    if args.output:
        open(args.output, 'wt').write(output + '\n')
    else:
        print(output)




def get_datasets(args, dataset_query):
    for dataset in args.datasets:
        if dataset_query == "":
            dataset_query = dataset
        else:
            dataset_query = dataset_query + " ," + dataset
    url = api_datasets_query % dataset_query
    datasets = d2.get(url.replace(" ", ""))
    return datasets


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('datasets', nargs='*', help='id of the dataset used by the indicators')
    add('-o', '--output', help='output file')
    add('-ig', '--indicatorGroups', default=False, help='print the indicators with its indicator group by name')
    add('-u', '--user', metavar='USER:PASSWORD', required=True,
        help='username and password for server authentication')
    add('--urlbase', default='https://extranet-uat.who.int/dhis2',
        help='base url of the dhis server')
    return parser.parse_args()


def id_list(a):  # we often get lists like [{'id': 'xxxx'}, {'id': 'yyyy'}, ...]
    return [x['id'] for x in a]


def get_simplified_indicators(dataelement_list, indicatorGroups):
    indicators = list()
    all_indicators = d2.get(api_simple_indicators_query)
    for indicator in all_indicators["indicators"]:
        get_indicator=False
        if indicator not in indicators:
            for uid in dataelement_list:
                if uid in indicator["denominator"] or uid in indicator["numerator"]:
                    get_indicator = True
        if get_indicator:
            indicator["indicatorGroupsNames"] = list()
            for indicatorgroupuids in indicator["indicatorGroups"]:
                for indicatorGroup in indicatorGroups["indicatorGroups"]:
                    if indicatorgroupuids["id"] == indicatorGroup["id"]:
                        indicator["indicatorGroupsNames"].append(indicatorGroup["name"])

            indicators.append(indicator)

    return describe_simplified_indicators(indicators)


def describe_simplified_indicators(indicator):
    indicators = list()
    for x in indicator:
        indicators.append(describe_simplified_indicators(x))
    return indicators


def describe_simplified_indicators(indicator):
    try:
        name = indicator['name']
        numerator = "numerator: " + indicator['numerator']
        denominator = "denominator: " + indicator['denominator']
        indicatorGroups = indicator["indicatorGroupsNames"]
        id = indicator['id']

        return {"name":name, "id":id, "numerator":numerator, "denominator":denominator, "indicatorGroups":indicatorGroups}
    except KeyError:
        return '***%s***' % indicator  # could not find it


def get_indicators(dataelement_list):
    indicators = list()
    all_indicators = d2.get(api_indicators_query)
    for indicator in all_indicators["indicators"]:
        include = False
        for uid in dataelement_list:
            if uid in indicator["denominator"] or uid in indicator["numerator"]:
                include = True
        if include:
                indicators.append(indicator)

    return indicators


def describe_indicators(indicator):
    indicators = list()
    for x in indicator:
        indicators.append(x)
    return indicators

if __name__ == '__main__':
    main()
