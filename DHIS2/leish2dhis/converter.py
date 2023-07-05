# Import the xlrd module
import json
import os
import subprocess
import requests

stop = "***** PLEASE DON'T MODIFY THESE HEADERS *****"
sheetsnames = ["Population", "VL", "CL", "ZCL"]
endemic_optionset = ["ENDEMIC", "ENDEMICITY_DOUBTFUL", "PREVIOUSLY_REPORTED_CASES", "AT_RISK",
                     "NO_AUTHOCHTHONOUS_CASES_REPORTED"]
progamstage_query = "/api/programs/%s.json?fields=programStages"
program_programstages = dict()
fixOrgUnits = dict()
fixOrgUnits["vGW4iEyxLOv"] = "N4ymCL5RSIn"
fixOrgUnits["HqKgvQhHoy3"] = "bbFCXdo5j9T"
fixOrgUnits["MSfuyy3tOQR"] = "uaDaMa0modO"
fixOrgUnits["ooXCq3ZBxaV"] = "KgbZAa1EPHg"
fixOrgUnits["DZZ125OWd8J"] = "cqBFwLIXRcH"
fixOrgUnits["rHzAyLOeTgS"] = "gkaY3mQeM0R"
fixOrgUnits["zlHkJUx9qql"] = "GLV6lqi0B0O"
fixOrgUnits["C81JPWWymfa"] = "B3zC2a6SXU8"

allOrgUnits = dict()


def getProgramStage(programid):
    user, password, server = connect_parameters()
    # Configurar las credenciales de autenticación básica
    credentials = (user, password)
    respuesta = requests.get(server + progamstage_query %  programid, auth=credentials)
    programstageid = json.loads(respuesta.text)["programStages"][0]["id"]
    # Verificar el resultado de la llamada
    if respuesta.status_code != 200:
        print('org unit: ' + programid + " error: " + str(respuesta.status_code) + "ou info: " + str(json.dumps(row)))
    return programstageid


def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return str(output).replace("b'", "").replace("\\n'", "")

# all orgunits
# https://extranet.who.int/dhis2-dev/api/organisationUnits.csv?fields=id,name,shortName,path,level&filter=level:lt:7&paging=false
# countries
# https://extranet.who.int/dhis2-dev/api/organisationUnits.csv?fields=id,name,shortName,path,level&filter=level:eq:3&paging=false

def getPos(letra):
    posicion = ord(letra) - 64
    return posicion - 1


def fixValue(value):
    if str(value).upper().replace(" ","") in endemic_optionset:
        return endemic_optionset.index(str(value).upper().replace(" ","")) + 1
    else:
        return value


def getData(dataelement, programid, period, type, orgunitid, value):
    if value is None or value == "":
        return None
    if orgunitid in fixOrgUnits.keys():
        orgunitid = fixOrgUnits[orgunitid]
    if type == "datasets":
        dhisvalue = {
            "dataElement": dataelement,
            "period": period,
            "orgUnit": orgunitid,
            "categoryOptionCombo": "Xr12mI7VPn3",
            "attributeOptionCombo": "Xr12mI7VPn3",
            "value": value,
            "storedBy": "leish2dhis script"}
    else:
        if programid not in program_programstages.keys():
            program_programstages[programid] = getProgramStage(programid)
        dhisvalue = {
                "programType": "WITHOUT_REGISTRATION",
                "orgUnit": orgunitid,
                "program": programid,
                "programStage": program_programstages[programid],
                "event": get_code(),
                "status": "ACTIVE",
                "eventDate": period,
                "occurredAt": period,
                "createdAt": period,
                "dataValues": [{
                    "storedBy": "leish2dhis script",
                    "dataElement": dataelement,
                    "occurredAt": period,
                    "createdAt": period,
                    "value": fixValue(value)
                }]}
    return dhisvalue


def getdate(period, pos):
    if pos<10:
        return str(period) + "-0" + str(pos) + "-01T00:00:00.000"
    else:
        return str(period) + "-" + str(pos) + "-01T00:00:00.000"


def checkOrgUnit(uid, row, credentials, server):

    # URL del recurso que se desea verificar si existe
    url = server + '/api/organisationUnits/' + uid

    # Realizar la llamada a la API
    respuesta = requests.get(url, auth=credentials)

    # Verificar el resultado de la llamada
    if respuesta.status_code != 200:
        print('org unit: ' + uid + " error: " + str(respuesta.status_code) + "ou info: " + str(json.dumps(row)))


def connect_parameters():
    import argparse

    # Create the parser object
    parser = argparse.ArgumentParser(description='Connect to a server using provided user and password')

    # Add the arguments
    parser.add_argument('--user', help='Username for server authentication', required=True)
    parser.add_argument('--password', help='Password for server authentication', required=True)
    parser.add_argument('--server', help='Server name or IP address', required=True)

    # Parse the arguments
    args = parser.parse_args()

    # Use the arguments to connect to the server
    print(f"Connecting to server {args.server} as user {args.user}")
    return args.user, args.password, args.server


ruta_directorio = "input"
archivos_xlsx = [archivo for archivo in os.listdir(ruta_directorio) if archivo.endswith(".xlsx")]

import openpyxl
totalDataValues= []
totalNormalProgram = []
totalAnormalProgram = []
for archivo in archivos_xlsx:
    ruta_archivo = os.path.join(ruta_directorio, archivo)

    obj = openpyxl.load_workbook(ruta_archivo)
    print(ruta_archivo)
    active_workbook = obj.active
    for sheetname in obj.sheetnames:
        sheetname = str(sheetname)
        print(sheetname)
        if sheetname == "Dictionary":
            continue
        try:
            sheet = obj[sheetname]
            table = [[cell.value for cell in row] for row in sheet.rows]

            period = ""
            dataelement = ""
            type = ""
            programid = ""
            count = 0
            dhis2data = []
            dhis2dataanormalevent = []
            while table[count][0] != stop:
                period = table[count][5]
                dataelement = table[count][2]
                type = table[count][4].lower()
                if type not in ["datasets", "programs"]:
                    print("type error; " +type)
                programid = table[count][3]
                letterStartPos = getPos(table[count][8])
                valuefirstrow = table[count][7]
                valuecellsnumber = table[count][9]

                count = count + 1

                for row in table[valuefirstrow-1:]:
                    orgunitid = row[0]

                    allOrgUnits[row[0]] = str(json.dumps(row)) + " filename: " + ruta_archivo
                    if valuecellsnumber == 1:
                        value = row[letterStartPos]
                        fixed_period = period
                        if (type == "programs"):
                            fixed_period = period + "-01-01T00:00:00.000"
                        dhis2value = getData(dataelement, programid, fixed_period, type, orgunitid, value)
                        if dhis2value is not None:
                            if type == "programs":
                                dhis2dataanormalevent.append(dhis2value)
                                totalAnormalProgram.append(dhis2value)
                            else:
                                dhis2data.append(dhis2value)
                                totalDataValues.append((dhis2value))
                    else:
                        for x in range(1, valuecellsnumber+1):
                            fixed_period = period
                            value = row[x + letterStartPos - 1]
                            if type == "programs":
                                fixed_period = getdate(period, x)
                            dhis2value = getData(dataelement, programid, fixed_period, type, orgunitid, value)
                            if dhis2value is not None:
                                dhis2data.append(dhis2value)
                                totalNormalProgram.append(dhis2value)
                resultanomalprogram = ""
                result = ""
                if type == "datasets":
                    result = {"dataValues": dhis2data}
                else:
                    result = {"events": dhis2data}
                    resultanomalprogram = {"events": dhis2dataanormalevent}

                # Serializing json
                json_object = json.dumps(result, indent=4)

                # Writing to sample.json
                with open("output/" + archivo.replace(".xlsx", "") + sheetname + ".json", "w") as outfile:
                    outfile.write(json_object)

                if len(dhis2dataanormalevent) > 0:
                    json_object = json.dumps(resultanomalprogram, indent=4)

                    # Writing to sample.json
                    with open("output/curl" + archivo.replace(".xlsx", "") + sheetname + ".json", "w") as outfile:
                        outfile.write(json_object)
        except Exception as e:
            print('Failed : '+ str(e))
            print("hoja no encontrada" + sheetname)
            print("fichejoero" + ruta_archivo)

json_object = json.dumps({"events":totalAnormalProgram}, indent=4)

# Writing to sample.json
with open("output/curl" + "rareprogram"+ ".json", "w") as outfile:
    outfile.write(json_object)


json_object = json.dumps({"events":totalNormalProgram}, indent=4)

# Writing to sample.json
with open("output/" + "normalprogram"+ ".json", "w") as outfile:
    outfile.write(json_object)


json_object = json.dumps({"dataValues":totalDataValues}, indent=4)

# Writing to sample.json
with open("output/" + "datavalues"+ ".json", "w") as outfile:
    outfile.write(json_object)



user, password, server = connect_parameters()
# Configurar las credenciales de autenticación básica
credentials = (user, password)


for orgunitkey in allOrgUnits.keys():
    if orgunitkey not in fixOrgUnits:
        checkOrgUnit(orgunitkey, allOrgUnits[orgunitkey], credentials, server)
    # n06IItYE45N dataelement VL_casees_by provenance_T	i5JSf4ffFl2	programs i5JSf4ffFl2	2016	pMukkUmnnkh
