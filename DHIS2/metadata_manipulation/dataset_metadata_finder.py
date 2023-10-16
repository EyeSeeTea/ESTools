#!/usr/bin/env python3

"""
Get a csv with all the dhis2 data elements and its category combo options in the given dataset
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import json
import dhis2 as d2
dataset_query = "dataSets/%s?fields=name,dataSetElements[dataElement[*]]"
default_category_combo = "Xr12mI7VPn3"

def main():
    args = get_args()
    d2.USER = args.user
    d2.URLBASE = args.urlbase
    rows = list()
    for dataset_uid in args.dataset:
        dataset = d2.get(dataset_query % dataset_uid)
        for data_set_element in dataset["dataSetElements"]:
            row = dict()
            data_element = data_set_element["dataElement"]
            row["name"] = data_element["name"]
            row["dataset"] = dataset["name"]
            if "code" in data_element.keys():
                row["code"] = data_element["code"]
            else:
                row["code"] = "no code"
            row["id"] = data_element["id"]
            category_combo = d2.get_object(data_element["categoryCombo"]["id"])
            row["topic"] = category_combo["name"]
            row["category_combo_options"] = list()
            for category_option_combo_id in category_combo["categoryOptionCombos"]:
                category_option_combo = d2.get_object(category_option_combo_id["id"])
                row["category_combo_options"].append({"name": category_option_combo["name"], "id": category_option_combo["id"]})
            rows.append(row)


    with open(args.output, mode='w') as file:
        csv_final_file = create_csv(file)
        for row in rows:
            for category_option_combo in row["category_combo_options"]:
                print([row["dataset"], row["name"], row["id"], row["code"], row["topic"],
                       category_option_combo["name"], category_option_combo["id"],default_category_combo, ""])
                csv_final_file.writerow([row["dataset"], row["name"], row["id"], row["code"], row["topic"],
                                         category_option_combo["name"], category_option_combo["id"],
                                         default_category_combo, ""])


def create_csv(file):
    import csv
    csv_final_file = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_final_file.writerow(['Module','Element','delid','code','Topic','Catcombo','catid','attid','Codes_version'])
    return csv_final_file

def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('-o', '--output', help='output file')
    add('-d', '--dataset', nargs='*', help='dataset id')
    add('-u', '--user', metavar='USER:PASSWORD', required=True,
        help='username and password for server authentication')
    add('--urlbase', default='https://extranet-uat.who.int/dhis2',
        help='base url of the dhis server')

    return parser.parse_args()

if __name__ == '__main__':
    main()
