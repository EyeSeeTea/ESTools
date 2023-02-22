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
        gghed_che = line[15]#duplicated
        tran_shi = line[26]
        che_ppp_pc = line[1200]
        gdp_ppp_pc = line[1419]
        fs5_che = line[1709]
        hf2_che = line[1725]
        hf3_che = line[1730]
        che_ncu2020_pc = line[2554]
        gghed_ncu2020_pc = line[2555] #duplicate
        gghed_ncu2020_pc = line[2555]
        gghed_gge=line[21]
        gghed_gdp=line[20]
        vhi_che=line[34]
        hf1_che=line[1717]
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
            datavalues.append({"dataElement": indicator_uid["gghed_che"], "value": gghed_che,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if hf2_che != '':
            datavalues.append({"dataElement": indicator_uid["hf2_che"], "value": hf2_che,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if hf3_che != '':
            datavalues.append({"dataElement": indicator_uid["hf3_che"], "value": hf3_che,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if che_ncu2020_pc != '':
            datavalues.append({"dataElement": indicator_uid["che_ncu2020_pc"], "value": che_ncu2020_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if gghed_ncu2020_pc != '':
            datavalues.append({"dataElement": indicator_uid["gghed_ncu2020_pc"], "value": gghed_ncu2020_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if fs5_che != '':
            datavalues.append({"dataElement": indicator_uid["fs5_che"], "value": fs5_che,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if gdp_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["gdp_ppp_pc"], "value": gdp_ppp_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if che_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["che_ppp_pc"], "value": che_ppp_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if tran_shi != '':
            datavalues.append({"dataElement": indicator_uid["tran_shi"], "value": tran_shi,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if oop_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["oop_ppp_pc"], "value": oop_ppp_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if gghed_gge != '':
            datavalues.append({"dataElement": indicator_uid["gghed_gge"], "value": gghed_gge,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if gghed_gdp != '':
            datavalues.append({"dataElement": indicator_uid["gghed_gdp"], "value": gghed_gdp,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if vhi_che != '':
            datavalues.append({"dataElement": indicator_uid["vhi_che"], "value": vhi_che,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if hf1_che != '':
            datavalues.append({"dataElement": indicator_uid["hf1_che"], "value": hf1_che,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if vhi_ncu2020_pc != '':
            datavalues.append({"dataElement": indicator_uid["vhi_ncu2020_pc"], "value": vhi_ncu2020_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if other_che != '':
            datavalues.append({"dataElement": indicator_uid["other_che"], "value": other_che,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if other_che != '':
            datavalues.append({"dataElement": indicator_uid["other_che"], "value": other_che,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if public_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["public_ppp_pc"], "value": public_ppp_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if public_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["public_ppp_pc"], "value": public_ppp_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if oop_ncu2020_pc != '':
            datavalues.append({"dataElement": indicator_uid["oop_ncu2020_pc"], "value": oop_ncu2020_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if vhi_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["vhi_ppp_pc"], "value": vhi_ppp_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })
        if public_ppp_pc != '':
            datavalues.append({"dataElement": indicator_uid["public_ppp_pc"], "value": public_ppp_pc,"orgunitname": orgunit, "code": code, "period": period+"0101","categoryOptionCombo": "Xr12mI7VPn3","attributeOptionCombo": "Xr12mI7VPn3" })

        datavalueset = {"dataValues":datavalues}
    count=count+1
  print(datavalueset)

  with open("output.json", "w") as write_file:
      json.dump(datavalueset, write_file)