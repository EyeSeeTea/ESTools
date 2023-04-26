import csv

dataelement1="CGk1OOt70Dz"

medicines="DGKEKA86rHV"
medicalproduct="yPye24hlTl4"
outpatient="BgxdKt8qtWf"
dental="AmIuGlRARZ5"
diagnosis="gFWp32SznUg"
inpatient="VFoIka0cyvK"

oumatcher = dict()

datavalues = list()
keys = dict()
with open('oecd1.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    count=0
    percentaje = "% of total population"

    for row in spamreader:
        orgunit = row[4]
        if row[3]!=percentaje:
            continue
        datavalues.append(
                        {
                            "dataElement": dataelement1,
                            "period": row[7],
                            "orgUnit": orgunit,
                            "categoryOptionCombo": "HllvX50cXC0",
                            "attributeOptionCombo": "HllvX50cXC0",
                            "value": row[8],
                            "storedBy": "script"
                        }
                    )

        count=count+1
#Filter "Country" to select the countries within our reach.
#Filter "Provider" with "All providers".
#Filter "Measure" with "Current prices".
#Filter the "financing scheme" with "All financing schemes" and "Government/compulsory schemes".
#Filter the following "Function":
# "Inpatient curative and rehabilitative care";
# "Outpatient curative care";
# "Dental outpatient curative care";
# "Ancillary services (non-specified by function);
# "Patient transportation";
# "Pharmaceuticals and other medical non-durable goods";
# "Therapeutic appliances and other medical durable goods".
# Customise the table adding "financing scheme" under "Year" and "function" under "Country".
# Then export as Excel. Convert all ".."
# into blank spaces.
dental="AmIuGlRARZ5"
inpatient="VFoIka0cyvK"
outpatient="BgxdKt8qtWf"
medicines="DGKEKA86rHV"
diagnosis="gFWp32SznUg"
medicalproduct="yPye24hlTl4"
def get_catopt(value):
    if value == "Dental outpatient curative care":
        return dental
    if value == "Inpatient curative and rehabilitative care":
        return inpatient
    if value == "Outpatient curative care":
        return outpatient
    if value == "Patient transportation":
        return diagnosis
    if value == "Pharmaceuticals and other medical non-durable goods":
        return medicines
    elif value == "Ancillary services (non-specified by function)":
        return "Ancillary"
    if value == "Therapeutic appliances and other medical durable goods":
        return medicalproduct
    else:
        print("error")
        return "error"
    pass

#1 financing
#3 function
#8 code
#11 year
#12 value


gobernance=dict()
voluntary=dict()
household=dict()
allfinances=dict()
" Voluntary health care payment schemes"
" Household out-of-pocket payments"
"Government/compulsory schemes"
dataelement2gob = "OE8u72wcKty"
dataelement3vol = "u8ZcWehUz9H"
dataelement4house = "S0rJgTIK3Gv"
allvalues = dict()
with open('alldata.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    count = 0
    for row in spamreader:
        if count ==0:
            count=count+1
            continue
        coc= get_catopt(row[3])
        #get the values to calculate the last one question
        if row[1] == "Voluntary health care payment schemes":
            voluntary[row[8]+"-"+row[11]+"-"+coc] = float(row[12])
        #get the values to calculate the last 2 one
        elif row[1] == "Government/compulsory schemes":
            gobernance[row[8] +"-"+ row[11] +"-"+ coc] = float(row[12])
        elif row[1] == "Household out-of-pocket payments":
            household[row[8] +"-"+ row[11] +"-"+ coc] = float(row[12])
        elif row[1] == "All financing schemes":
            allfinances[row[8] +"-"+ row[11] +"-"+ coc] = float(row[12])
            continue

            # for medicines we use "Pharmaceuticals and other medical non-durable goods";
            # for Medical products we use "Therapeutic appliances and other medical durable goods;
            # for Outpatient care we use the substraction of "outpatient curative care"
            # and "Dental outpatient curative care";
            # for dental care we use "Dental outpatient curative care";
            # for diagnostic tests we use the substraction of "Ancillary services (non-specified by function)
            # and "Patient transportation";
            # for inpatient care we use "Inpatient curative and rehabilitative care".
            # Divided "Government/compulsory schemes" / "All financing schemes" and multiply by 100

    with open('alldata.csv', newline='') as csvfile2:
        spamreader2 = csv.reader(csvfile2, delimiter=',')
        count = 0
        for row in spamreader2:
            if count ==0:
                count=count+1
                continue
            else:
                coc= get_catopt(row[3])
                if row[1] == "All financing schemes":

                    key = row[8] + "-" + row[11] + "-" + coc
                    if row[3] == "Dental outpatient curative care":
                        if key in gobernance:
                            value = (gobernance[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement2gob] = value

                        if key in voluntary:
                            value = (voluntary[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement3vol] = value

                        if key in household:
                            value = (household[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement4house] = value
                    if row[3] == "Pharmaceuticals and other medical non-durable goods":
                        if key in gobernance:
                            value = (gobernance[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement2gob] = value

                        if key in voluntary:
                            value = (voluntary[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement3vol] = value

                        if key in household:
                            value = (household[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement4house] = value
                    if row[3] == "Therapeutic appliances and other medical durable goods":
                        if key in gobernance:
                            value = (gobernance[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement2gob] = value

                        if key in voluntary:
                            value = (voluntary[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement3vol] = value

                        if key in household:
                            value = (household[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement4house] = value
                    if row[3] == "Inpatient curative and rehabilitative care":
                        if key in gobernance:
                            value = (gobernance[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement2gob] = value

                        if key in voluntary:
                            value = (voluntary[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement3vol] = value

                        if key in household:
                            value = (household[key] / float(row[12]))*100
                            allvalues[key+"-"+dataelement4house] = value
                    if get_catopt(row[3]) == "Ancillary":
                        keycoc=row[8] + "-" +  row[11] + "-" +  coc
                        keypatientcoc=row[8] + "-" +  row[11] + "-" +  get_catopt("Patient transportation" )
                        if keycoc in allfinances.keys() and keycoc in gobernance.keys() and keycoc in voluntary.keys() and keycoc in household.keys() and keypatientcoc in allfinances.keys() and keypatientcoc in gobernance.keys() and keypatientcoc in voluntary.keys() and keypatientcoc in household.keys():
                            patient_all = allfinances[keypatientcoc]
                            patient_gob = gobernance[keypatientcoc]
                            patient_vol = voluntary[keypatientcoc]
                            patient_house = household[keypatientcoc]
                            ancillary_gob = gobernance[keycoc]
                            ancillary_vol = voluntary[keycoc]
                            ancillary_house = household[keycoc]
                            ancillary_all = allfinances[keycoc]
                            patient_value_gob = (gobernance[keypatientcoc] / float(patient_all)) * 100
                            patient_value_vol = (voluntary[keypatientcoc] / float(patient_all)) * 100
                            patient_value_house = (household[keypatientcoc] / float(patient_all)) * 100

                            ancillary_value_gob = (gobernance[keycoc] / float(ancillary_all)) * 100
                            ancillary_value_vol = (voluntary[keycoc] / float(ancillary_all)) * 100
                            ancillary_value_house = (household[keycoc] / float(ancillary_all)) * 100

                            allvalues[keypatientcoc + "-" + dataelement2gob] = ancillary_value_gob - patient_value_gob
                            allvalues[keypatientcoc+ "-" + dataelement3vol] = ancillary_value_vol - patient_value_vol
                            allvalues[keypatientcoc + "-" + dataelement4house] = ancillary_value_house - patient_value_house


                    if row[3] == "Outpatient curative care":
                        dentcoc =  get_catopt("Dental outpatient curative care" )
                        keycoc=row[8] +"-"+ row[11] +"-"+ coc
                        keydentcoc=row[8] +"-"+ row[11] +"-"+ dentcoc
                        if keycoc in allfinances.keys() and keycoc in gobernance.keys() and keycoc in voluntary.keys() and keycoc in household.keys() and dentcoc in allfinances.keys() and dentcoc in gobernance.keys() and dentcoc in voluntary.keys() and dentcoc in household.keys():
                            outpatient_all = allfinances[keycoc]
                            outpatient_gob = gobernance[keycoc]
                            outpatient_vol = voluntary[keycoc]
                            outpatient_house = household[keycoc]

                            dent_gob = gobernance[keydentcoc]
                            dent_vol = voluntary[keydentcoc]
                            dent_house = household[keydentcoc]
                            dent_all = allfinances[keydentcoc]
                            outpatient_value_gob = (gobernance[keycoc] / float(outpatient_all)) * 100
                            outpatient_value_vol = (voluntary[keycoc] / float(outpatient_all)) * 100
                            outpatient_value_house = (household[keycoc] / float(outpatient_all)) * 100

                            dent_value_gob = (gobernance[keydentcoc] / float(dent_all)) * 100
                            dent_value_vol = (voluntary[keydentcoc] / float(dent_all)) * 100
                            dent_value_house = (household[keydentcoc] / float(dent_all)) * 100

                            allvalues[keycoc + "-" + dataelement2gob] = outpatient_value_gob - dent_value_gob
                            allvalues[keycoc + "-" + dataelement3vol] =  outpatient_value_vol - dent_value_vol
                            allvalues[keycoc + "-" + dataelement4house] =  outpatient_value_house - dent_value_house



            count = count + 1

for valuekey in allvalues.keys():
    value = allvalues[valuekey]
    keys = valuekey.split("-")
    if keys[0] == "USA":
        continue
    datavalues.append(
        {
            "dataElement": keys[3],
            "period": keys[1],
            "orgUnit": keys[0],
            "categoryOptionCombo": keys[2],
            "attributeOptionCombo": "HllvX50cXC0",
            "value": format(value, '.2f'),
            "storedBy": "script"
        }
    )


import json
with open('newvalues2.json', 'w') as f:
    json.dump({"dataValues":datavalues}, f, sort_keys=True, indent=4)