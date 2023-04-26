
dataelement=""
dataelement_dent= "O6QzuV156GP-HllvX50cXC0-val"
dataelement_dentless= "GOAVPNZCUB9-HllvX50cXC0-val"
dataelement_dentmost= "KywDZVw2WHD-HllvX50cXC0-val"
dataelement_dent64= "mEEtuRmC9sU-HllvX50cXC0-val"
dataelement_med= "egU3Cc86amd-HllvX50cXC0-val"
dataelement_medless= "y0kRMifSf8V-HllvX50cXC0-val"
dataelement_medmost= "OqEzvjBe6Cs-HllvX50cXC0-val"
dataelement_med64= "yu1GFGkSBKa-HllvX50cXC0-val"
dataelement_pmeds= "GyiW7dS7BIl-HllvX50cXC0-val"
dataelement_pmedsless= "q2kdsUWt3q7-HllvX50cXC0-val"
dataelement_pmedsmost= "OOoBKomdEOO-HllvX50cXC0-val"
dataelement_pmeds64= "Kq0QsqIAaUd-HllvX50cXC0-val"
ed2="ED0-2"
ed3="ED3-4"
edtotal="TOTAL"
y16="TOTAL"
y64="Y_GE65"
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
with open('../input/hlth_ehis_un2e__custom_5612239_linear.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    count=0
    for row in spamreader:
        if count>0:
            catoptcomb= row[4]
            if catoptcomb == "HC_DENT":
                if row[5] == "ED0-2":
                    if row[7]=="TOTAL":
                        catoptcomb = dataelement_dentless.split("-")[1]
                        dataelement = dataelement_dentless.split("-")[0]
                elif row[5] == "ED3_4":
                    if row[7]=="TOTAL":
                        catoptcomb = dataelement_dentmost.split("-")[1]
                        dataelement = dataelement_dentmost.split("-")[0]
                elif row[5] == "TOTAL":
                    if row[7]=="TOTAL":
                        catoptcomb = dataelement_dent.split("-")[1]
                        dataelement = dataelement_dent.split("-")[0]
                    elif row[7]=="Y_GE65":
                        catoptcomb = dataelement_dent64.split("-")[1]
                        dataelement = dataelement_dent64.split("-")[0]
            elif catoptcomb == "HC_MED":
                if row[5] == "ED0-2":
                    if row[7]=="TOTAL":
                        catoptcomb = dataelement_medless.split("-")[1]
                        dataelement = dataelement_medless.split("-")[0]
                elif row[5] == "ED3_4":
                    if row[7]=="TOTAL":
                        catoptcomb = dataelement_medmost.split("-")[1]
                        dataelement = dataelement_medmost.split("-")[0]
                elif row[5] == "TOTAL":
                    if row[7]=="TOTAL":
                        catoptcomb = dataelement_med.split("-")[1]
                        dataelement = dataelement_med.split("-")[0]
                    elif row[7]=="Y_GE65":
                        catoptcomb = dataelement_med64.split("-")[1]
                        dataelement = dataelement_med64.split("-")[0]
            elif catoptcomb == "MG_PMEDS":
                if row[5] == "ED0-2":
                    if row[7]=="TOTAL":
                        catoptcomb = dataelement_pmedsless.split("-")[1]
                        dataelement = dataelement_pmedsless.split("-")[0]
                elif row[5] == "ED3_4":
                    if row[7]=="TOTAL":
                        catoptcomb = dataelement_pmedsmost.split("-")[1]
                        dataelement = dataelement_pmedsmost.split("-")[0]
                elif row[5] == "TOTAL":
                    if row[7]=="TOTAL":
                        catoptcomb = dataelement_pmeds.split("-")[1]
                        dataelement = dataelement_pmeds.split("-")[0]
                    elif row[7]=="Y_GE65":
                        catoptcomb = dataelement_pmeds64.split("-")[1]
                        dataelement = dataelement_pmeds64.split("-")[0]
            else:
                print("not match!")
            oucode = row[8]
            period = row[9]
            value = row[10]
            if oucode in oumatcher.keys():
                if dataelement+period+oumatcher[oucode]+catoptcomb in keys.keys():
                    print("duplicate" + dataelement+period+oumatcher[oucode]+catoptcomb)
                    print("values" + str(value) +row[7] + " other "+ keys[dataelement+period+oumatcher[oucode]+catoptcomb])
                else:
                    keys[dataelement + period + oumatcher[oucode] + catoptcomb] = row[7]
                if catoptcomb not in ["MG_PMEDS","HC_MED","HC_DENT"]:
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
with open('../outputlastupdated.json', 'w') as f:
    json.dump({"dataValues":datavalues}, f, sort_keys=True, indent=4)