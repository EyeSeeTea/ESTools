
dataelement="CQq6HWprR0p"
dataelement_total="Wm2v9VGGSuK-HllvX50cXC0-val"
dataelement_porest="a2zFSqU1Zsb-Rh9j1wC8hNt-val"
dataelement_richest="a2zFSqU1Zsb-ut4ntetvGMW-val"
dataelement_64years="CqwZui9SRJF-HllvX50cXC0-val"
y16="Y_GE16"
y64="Y_GE65"
poorest="fcEivvOxZrY"

level2="KoycbPPMxMc"
level3="CFaiDiKYWfp"
level4="RLofI9X8Pgl"
level5="KlRimmMdZ7l"
total="gEWtgad4feW"
oumatcher = dict()

datavalues = list()
import csv
with open('../OUMATCH.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    count=0
    for row in spamreader:
        if count>0:
            oumatcher[row[0]]=row[2]
        else:
            print(', '.join(row))
        count=count+1
8
with open('../input/hlth.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    count=0
    for row in spamreader:
        if count>0:
            catoptcomb= row[4]
            if catoptcomb == "QU1":
                if row[6]==y16:
                    catoptcomb = dataelement_porest.split("-")[1]
                    dataelement = dataelement_porest.split("-")[0]
            elif catoptcomb == "QU5":
                if row[6]==y16:
                    catoptcomb = dataelement_richest.split("-")[1]
                    dataelement = dataelement_richest.split("-")[0]
            elif catoptcomb == "TOTAL":
                if row[6]==y16:
                    catoptcomb = dataelement_total.split("-")[1]
                    dataelement = dataelement_total.split("-")[0]
                elif row[6]==y64:
                    catoptcomb = dataelement_64years.split("-")[1]
                    dataelement = dataelement_64years.split("-")[0]
            else:
                print("not match!")
            oucode = row[8]
            period = row[9]
            value = row[10]
            if oucode in oumatcher.keys():
                if catoptcomb not in ["QU1","QU5"]:
                    print(
                        {
                            "dataElement": dataelement,
                            "period": period,
                            "orgUnit": oumatcher[oucode],
                            "categoryOptionCombo": catoptcomb,
                            "attributeOptionCombo": "HllvX50cXC0",
                            "value": value,
                            "storedBy": "script"
                        })
                    datavalues.append(
                        {
                            "dataElement": dataelement,
                            "period": period,
                            "orgUnit": oumatcher[oucode],
                            "categoryOptionCombo": catoptcomb,
                            "attributeOptionCombo": "HllvX50cXC0",
                            "value": value,
                            "storedBy": "script"
                        }
                    )
        else:
            print(', '.join(row))
        count=count+1



import json
with open('../outputfixeddent.json', 'w') as f:
    json.dump({"dataValues":datavalues}, f, sort_keys=True, indent=4)