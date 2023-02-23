# Import the xlrd module
import json
filename = "Republic of Tunisia_Population_VL_CL_Dictionary_2016_ADM1+data.xlsx"
stop="***** PLEASE DON'T MODIFY THESE HEADERS *****"
sheetsnames = ["Population", "VL", "CL"]
#all orgunits
#https://extranet.who.int/dhis2-dev/api/organisationUnits.csv?fields=id,name,shortName,path,level&filter=level:lt:7&paging=false
#countries
#https://extranet.who.int/dhis2-dev/api/organisationUnits.csv?fields=id,name,shortName,path,level&filter=level:eq:3&paging=false

def getPos(letra):
    posicion = ord(letra) - 64
    return posicion-1

def getData(dataelement, programid, period, type, orgunitid, value):
    if value is None:
        return None
    if type == "datasets":
        dhisvalue = {
            "dataElement": dataelement,
            "period": period,
            "orgUnit": orgunitid,
            "categoryOptionCombo": "Xr12mI7VPn3",
            "attributeOptionCombo": "Xr12mI7VPn3",
            "value": row[6],
            "storedBy": "leish2dhis script"}
    else:
        dhisvalue = {
            "programType": "WITHOUT_REGISTRATION",
            "orgUnit": orgunitid,
            "program": programid,
            "status": "ACTIVE",
            "eventDate": period ,
            "dataValues": [{
                "storedBy": "leish2dhis script",
                "dataElement": dataelement,
                "value": value
            }]}
    return dhisvalue

import openpyxl

obj = openpyxl.load_workbook("input/"+filename)


def getdate(period, pos):
    return str(period)+ "-" + str(pos)+"-01T00:00:00.000"


for sheetname in sheetsnames:
    print(sheetname)
    sheet = obj.get_sheet_by_name(sheetname)
    table = [[cell.value for cell in row] for row in sheet.rows]

    period = ""
    dataelement = ""
    type = ""
    programid = ""
    count = 0
    dhis2data =[]
    while table[count][0] != stop:
        period = table[count][5]
        dataelement = table[count][2]
        type = table[count][4]
        programid= table[count][3]
        letterStartPos = getPos(table[count][8])
        valuefirstrow = table[count][7]
        valuecellsnumber = table[count][9]

        count=count+1
            #mKpmhDgK4Cq(dataElements GEN_pop_Leish)	deKCGAGoEHz	dataSet Population data	2016	pMukkUmnnkh




        for row in table[valuefirstrow:]:
            orgunitid = row[0]
            if valuecellsnumber == 1:
                value = row[letterStartPos]
                fixed_period = period
                if (type == "programs"):
                    fixed_period = period + "-01-01T00:00:00.000"
                dhis2value = getData(dataelement, programid,period,type,orgunitid,value)
            else:
                for x in range(1, valuecellsnumber):
                    fixed_period = period
                    value = row[x+letterStartPos-1]
                    if type == "programs":
                        fixed_period = getdate(period, x)
                    dhis2value = getData(dataelement, programid, fixed_period, type, orgunitid, value)
            if dhis2value is not None:
                dhis2data.append(dhis2value)


        result=""
        if type == "datasets":
            result = {"dataValues": dhis2data}
        else:
            if "events" in result:
                result = {"events": result["events"].appdhis2data}
            else:
                result = {"events": dhis2data}

        # Serializing json
        json_object = json.dumps(result, indent=4)

        # Writing to sample.json
        with open("output/"+filename.replace(".xlsx","")+sheetname+".json", "w") as outfile:
            outfile.write(json_object)
#n06IItYE45N dataelement VL_cases_by provenance_T	i5JSf4ffFl2	programs i5JSf4ffFl2	2016	pMukkUmnnkh

