
dataelement="CQq6HWprR0p"
dataelement_total="CQq6HWprR0p-HllvX50cXC0-val"#chk
dataelement_porest="Ks2z3Tx4SE5-Rh9j1wC8hNt-val"
dataelement_richest="Ks2z3Tx4SE5-ut4ntetvGMW-val"
dataelement_64years="COYhXNaR62J-HllvX50cXC0-val"#chk
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
keys = dict()
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
with open('../input/hlth_silc_08__custom_5611565_linear.csv', newline='') as csvfile:
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
                if dataelement+period+oumatcher[oucode]+catoptcomb in keys.keys():
                    print("duplicate" + dataelement+period+oumatcher[oucode]+catoptcomb)
                    print("values" + str(value) +" other "+ keys[dataelement+period+oumatcher[oucode]+catoptcomb] )
                else:
                    keys[dataelement + period + oumatcher[oucode] + catoptcomb] = value

                if catoptcomb not in ["QU1","QU5"]:
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
with open('../output_searchdup.json', 'w') as f:
    json.dump({"dataValues":datavalues}, f, sort_keys=True, indent=4)