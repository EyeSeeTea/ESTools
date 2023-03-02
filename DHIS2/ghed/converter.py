import csv
import json

# opening the CSV file
indicator_uid = dict()
uid_indicator = dict()
indicator_position = dict()
headers = dict()

with open('mapperGHED.csv', mode='r') as file:
    # reading the CSV file
    csvFile = csv.reader(file)

    # displaying the contents of the CSV file
    count = 0
    for line in csvFile:
        if count > 0:
            uid_indicator[line[1]] = line[0]
            indicator_uid[line[0]] = line[1]
            print(line)

        count = count + 1

new_list = []


def getFloat(value):
    if value == "":
        return 0
    else:
        return float(value.replace(",", "."))


with open('GHED_datas.csv', mode='r') as file:
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
                    indicator_position[col] = countcol
                countcol = countcol + 1
        if count > 0:
            orgunit = line[0]
            code = line[1]
            period = line[4]
            gghed_che = line[indicator_position["gghed_che"]].replace(".", "").replace(",", ".")  # duplicated
            tran_shi = line[indicator_position["tran_shi"]].replace(".", "").replace(",", ".")
            che_ppp_pc = line[indicator_position["che_ppp_pc"]].replace(".", "").replace(",", ".")
            gdp_ppp_pc = line[indicator_position["gdp_ppp_pc"]].replace(".", "").replace(",", ".")
            fs5_che = line[indicator_position["fs5_che"]].replace(".", "").replace(",", ".")
            hf2_che = line[indicator_position["hf2_che"]].replace(".", "").replace(",", ".")
            hf3_che = line[indicator_position["hf3_che"]].replace(".", "").replace(",", ".")
            che_ncu2020_pc = line[indicator_position["che_ncu2020_pc"]].replace(".", "").replace(",", ".")
            gghed_ncu2020_pc = line[indicator_position["gghed_ncu2020_pc"]].replace(".", "").replace(",", ".")
            gghed_gge = line[indicator_position["gghed_gge"]].replace(".", "").replace(",", ".")
            gghed_gdp = line[indicator_position["gghed_gdp"]].replace(".", "").replace(",", ".")
            vhi_che = line[indicator_position["vhi_che"]].replace(".", "").replace(",", ".")
            hf1_che = line[indicator_position["hf1_che"]].replace(".", "").replace(",", ".")
            fs3_che = line[indicator_position["fs3_che"]].replace(".", "").replace(",", ".")
            fs11_che = line[indicator_position["fs11_che"]].replace(".", "").replace(",", ".")
            public_ppp_pc = ""  # Public spending on health per person in current PPP
            vhi_ncu2020_pc = ""  # Voluntary health insurance spending per person in constant NCU
            vhi_ppp_pc = ""  # Voluntary health insurance spending per person in current PPP
            oop_ncu2020_pc = ""  # Out-of-pocket payments per person in constant NCU
            oop_ppp_pc = ""  # Out-of-pocket payments per person in current PPP
            oop_che = ""  # duplicate Out-of-pocket payments as a share of current spending on health
            public_ppp_pc = ""  # duplicate Public spending on health per person in current PPP
            public_ppp_pc = ""  # Public spending on health per person in current PPP
            oop_che = ""  # Out-of-pocket payments as a share of current spending on health # "Health spending(health accounts)"    Breakdown of current spending on health by financing scheme
            # gghed_ncu2020_pc public_ppp_pc vhi_ncu2020_pc vhi_ppp_pc oop_ncu2020_pc oop_ppp_pc "Health spending(health accounts)"    Health spending per person  by financing scheme

            other_che = ""
            if gghed_che != "" and fs5_che != "" and oop_che != "":
                other_che = str(100 - (getFloat(gghed_che) + getFloat(fs5_che) + getFloat(
                    oop_che)))  # 100-(gghed_che + fs5_che + oop_che)
            if fs3_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["fs3_che"], "value": fs3_che, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if fs11_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["fs11_che"], "value": fs11_che, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if gghed_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["gghed_che"], "value": gghed_che, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if hf2_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["hf2_che"], "value": hf2_che, "orgunitname": orgunit, "orgUnit": code,
                     "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if hf3_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["hf3_che"], "value": hf3_che, "orgunitname": orgunit, "orgUnit": code,
                     "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if che_ncu2020_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["che_ncu2020_pc"], "value": che_ncu2020_pc.replace(".", ""),
                     "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if gghed_ncu2020_pc != '':
                datavalues.append({"dataElement": indicator_uid["gghed_ncu2020_pc"], "value": gghed_ncu2020_pc,
                                   "orgunitname": orgunit, "orgUnit": code, "period": period,
                                   "categoryOptionCombo": "HllvX50cXC0", "attributeOptionCombo": "HllvX50cXC0"})
            if fs5_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["fs5_che"], "value": fs5_che, "orgunitname": orgunit, "orgUnit": code,
                     "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if gdp_ppp_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["gdp_ppp_pc"], "value": gdp_ppp_pc, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if che_ppp_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["che_ppp_pc"], "value": che_ppp_pc, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if tran_shi != '':
                datavalues.append(
                    {"dataElement": indicator_uid["tran_shi"], "value": tran_shi, "orgunitname": orgunit, "orgUnit": code,
                     "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if oop_ppp_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["oop_ppp_pc"], "value": oop_ppp_pc, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if gghed_gge != '':
                datavalues.append(
                    {"dataElement": indicator_uid["gghed_gge"], "value": gghed_gge, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if gghed_gdp != '':
                datavalues.append(
                    {"dataElement": indicator_uid["gghed_gdp"], "value": gghed_gdp, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if vhi_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["vhi_che"], "value": vhi_che, "orgunitname": orgunit, "orgUnit": code,
                     "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if hf1_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["hf1_che"], "value": hf1_che, "orgunitname": orgunit, "orgUnit": code,
                     "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if vhi_ncu2020_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["vhi_ncu2020_pc"], "value": vhi_ncu2020_pc, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if other_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["other_che"], "value": other_che, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if other_che != '':
                datavalues.append(
                    {"dataElement": indicator_uid["other_che"], "value": other_che, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if public_ppp_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["public_ppp_pc"], "value": public_ppp_pc, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if public_ppp_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["public_ppp_pc"], "value": public_ppp_pc, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if oop_ncu2020_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["oop_ncu2020_pc"], "value": oop_ncu2020_pc, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if vhi_ppp_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["vhi_ppp_pc"], "value": vhi_ppp_pc, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})
            if public_ppp_pc != '':
                datavalues.append(
                    {"dataElement": indicator_uid["public_ppp_pc"], "value": public_ppp_pc, "orgunitname": orgunit,
                     "orgUnit": code, "period": period, "categoryOptionCombo": "HllvX50cXC0",
                     "attributeOptionCombo": "HllvX50cXC0"})

        datavalueset = {"dataValues": datavalues}
        count = count + 1
    print(datavalueset)

    with open("output.json", "w") as write_file:
        json.dump(datavalueset, write_file)
