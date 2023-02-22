import csv
import json

# opening the CSV file
indicator_uid = dict()
uid_indicator = dict()
indicator_position = dict()
headers = dict()

with open('mapperGHED.csv', mode ='r') as file:
   
  # reading the CSV file
  csvFile = csv.reader(file)
 
  # displaying the contents of the CSV file
  count = 0
  for line in csvFile:
    if count>0:
        uid_indicator[line[1]] = line[0]
        indicator_uid[line[0]] = line[1]
        print(line)
    
    count=count+1

new_list= []
with open('GHED_datas.csv', mode ='r')as file:
   
  # reading the CSV file
  csvFile = csv.reader(file, delimiter=";")
 
  # displaying the contents of the CSV file
  count = 0

  datavalues = []
  for line in csvFile:
    if count == 0:
        countcol = 0
        for col in line:
            if col in uid_indicator.values():
                indicator_position[col]=countcol
            countcol=countcol+1
    if count>0:
        orgunit = line[0]
        code = line[1]
        period = line[4]
        gghed_che = line[15].replace(",",".")#duplicated
        tran_shi = line[26].replace(",",".")
        che_ppp_pc = line[1200].replace(",",".")
        gdp_ppp_pc = line[1419].replace(",",".")
        fs5_che = line[1709].replace(",",".")
        hf2_che = line[1725].replace(",",".")
        hf3_che = line[1730].replace(",",".")
        che_ncu2020_pc = line[2554].replace(",",".")
        gghed_ncu2020_pc = line[2555].replace(",",".") #duplicate
        gghed_ncu2020_pc = line[2555].replace(",",".")
        gghed_gge=line[21].replace(",",".")
        gghed_gdp=line[20].replace(",",".")
        vhi_che=line[34].replace(",",".")
        hf1_che=line[1717].replace(",",".")
        public_ppp_pc = ""
        vhi_ppp_pc = ""
        oop_ncu2020_pc = ""
        public_ppp_pc = ""#duplicate
        public_ppp_pc = ""
        oop_che=""#duplicate
        oop_che=""
        oop_ppp_pc = ""
        vhi_ncu2020_pc=""
        other_che=""
        if gghed_che != '':
            datavalues.append({"dataElement": indicator_uid["gghed_che"], "value": gghed_che,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if hf2_che != '':
            datavalues.append({"dataElement": indicator_uid["hf2_che"], "value": hf2_che,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if hf3_che != '':
            datavalues.append({"dataElement": indicator_uid["hf3_che"], "value": hf3_che,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if che_ncu2020_pc != '':
            datavalues.append({"dataElement": indicator_uid["che_ncu2020_pc"], "value": che_ncu2020_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if gghed_ncu2020_pc != '':
            datavalues.append({"dataElement": indicator_uid["gghed_ncu2020_pc"], "value": gghed_ncu2020_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if fs5_che != '':
            datavalues.append({"dataElement": indicator_uid["fs5_che"], "value": fs5_che,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if gdp_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["gdp_ppp_pc"], "value": gdp_ppp_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if che_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["che_ppp_pc"], "value": che_ppp_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if tran_shi != '':
            datavalues.append({"dataElement": indicator_uid["tran_shi"], "value": tran_shi,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if oop_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["oop_ppp_pc"], "value": oop_ppp_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if gghed_gge != '':
            datavalues.append({"dataElement": indicator_uid["gghed_gge"], "value": gghed_gge,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if gghed_gdp != '':
            datavalues.append({"dataElement": indicator_uid["gghed_gdp"], "value": gghed_gdp,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if vhi_che != '':
            datavalues.append({"dataElement": indicator_uid["vhi_che"], "value": vhi_che,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if hf1_che != '':
            datavalues.append({"dataElement": indicator_uid["hf1_che"], "value": hf1_che,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if vhi_ncu2020_pc != '':
            datavalues.append({"dataElement": indicator_uid["vhi_ncu2020_pc"], "value": vhi_ncu2020_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if other_che != '':
            datavalues.append({"dataElement": indicator_uid["other_che"], "value": other_che,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if other_che != '':
            datavalues.append({"dataElement": indicator_uid["other_che"], "value": other_che,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if public_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["public_ppp_pc"], "value": public_ppp_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if public_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["public_ppp_pc"], "value": public_ppp_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if oop_ncu2020_pc != '':
            datavalues.append({"dataElement": indicator_uid["oop_ncu2020_pc"], "value": oop_ncu2020_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if vhi_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["vhi_ppp_pc"], "value": vhi_ppp_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })
        if public_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["public_ppp_pc"], "value": public_ppp_pc,"orgUnitname": orgunit, "orgUnit": code, "period": period+"0101","categoryOptionCombo": "HllvX50cXC0","attributeOptionCombo": "HllvX50cXC0" })

        datavalueset = {"dataValues":datavalues}
    count=count+1
  print(datavalueset)

  with open("output.json", "w") as write_file:
      json.dump(datavalueset, write_file)