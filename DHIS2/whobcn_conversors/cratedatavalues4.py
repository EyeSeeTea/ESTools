import csv

dataelement1="KYQFtysBDHr"
dataelement2= "OKMPX14j9Pk"
oumatcher = dict()

datavalues = list()
keys = dict()
8
with open('../SDG3.8.1.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    count=0
    for row in spamreader:
        datavalues.append(
                        {
                            "dataElement": dataelement1,
                            "period": row[5],
                            "orgUnit": row[2],
                            "categoryOptionCombo": "HllvX50cXC0",
                            "attributeOptionCombo": "HllvX50cXC0",
                            "value": row[6],
                            "storedBy": "script"
                        }
                    )

        count=count+1

with open('../SDG3.8.2.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    count = 0
    for row in spamreader:
        datavalues.append(
            {
                "dataElement": dataelement2,
                "period": row[5],
                "orgUnit": row[3],
                "categoryOptionCombo": "HllvX50cXC0",
                "attributeOptionCombo": "HllvX50cXC0",
                "value": row[6],
                "storedBy": "script"
            }
        )

        count = count + 1


import json
with open('../newvalues.json', 'w') as f:
    json.dump({"dataValues":datavalues}, f, sort_keys=True, indent=4)