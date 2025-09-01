import json
import xlrd
from d2apy import dhis2api
#How-to
#download the google doc file as excel
#open excel file and convert to xls
#Change loc value by the excel file
#Change lang by the lang
#In the case of covid, the "QUESTION" rows are called " questions" and in PAHO only "question",
# we must change that before run in line 81. Now is paho style.
# Give the location of the file
loc = ('PAHO_nl.xls')
lang = "nl"
translation = {"translations":[
    {"property":"FORM_NAME","locale":lang, "value": ""},
    {"property":"NAME","locale":lang, "value":""},
    {"property":"DESCRIPTION","locale":lang, "value":""},
    {"property":"SHORT_NAME","locale":lang, "value":""}]}

# To open Workbook
wb = xlrd.open_workbook(loc)
sheetsrange = range(wb.nsheets)

def init_api(url, username, password):
    return dhis2api.Dhis2Api(url, username, password)

api = init_api("http://localhost:8080/", "admin", "district")

options = list()
dataelements = list()
trackedentityattributes = list()
programstages = list()
programs = list()
programstagesections = list()


def insert_or_update_item(object, property, value):
    if value != "":
        exist = False
        for translation in object["translations"]:
            if translation["property"] == property and translation["locale"] == lang:
                translation["value"] = value
                return object
        if not exist:
            object["translations"].append({"property": property, "locale": lang, "value": value})
    return  object


for n in sheetsrange:
    sheet = wb.sheet_by_index(n)
    print(sheet.name)
    rowsrange = range(sheet.nrows)
    for i in rowsrange:
        if i==0:
            continue
        if sheet.name == "Options":
            uid = sheet.row_values(i)[0]
            name_translated = sheet.row_values(i)[4]
            option = api.get("/options/"+uid+".json?fields=*")
            option = insert_or_update_item(option, "NAME", name_translated)
            options.append(option)
        elif "form info" in sheet.name.lower() and "General Info" not in sheet.name:
            uid = sheet.row_values(i)[0]
            name_translated = sheet.row_values(i)[7]
            formname_translated = sheet.row_values(i)[3]
            description_translated = sheet.row_values(i)[5]
            shortname_translated = sheet.row_values(i)[9]
            type = sheet.row_values(i)[10].lower()
            if type == "section":
                programstagesection = api.get("/programStageSections/" + uid + ".json?fields=*")
                programstagesection = insert_or_update_item(programstagesection, "NAME", name_translated)
                programstagesection = insert_or_update_item(programstagesection, "DESCRIPTION", description_translated)
                programstagesection = insert_or_update_item(programstagesection, "SHORT_NAME", shortname_translated)
                programstagesections.append(programstagesection)
            elif type == "form":
                programstage = api.get("/programStages/" + uid + ".json&fields=*")

                programstage = insert_or_update_item(programstage, "NAME", name_translated)
                programstage = insert_or_update_item(programstage, "DESCRIPTION", description_translated)
                programstages.append(programstage)
            else:
                print(str(i)+"not found "+ uid)
        elif "Questions" in sheet.name:
            uid = sheet.row_values(i)[0]
            if uid == "":
                continue
            formname_translated = sheet.row_values(i)[8]
            description_translated = sheet.row_values(i)[10]
            dataelement = api.get("/dataElements/"+uid+".json?fields=*")
            dataelement = insert_or_update_item(dataelement, "DESCRIPTION", description_translated)
            dataelement = insert_or_update_item(dataelement, "FORM_NAME", formname_translated)
            dataelements.append(dataelement)
        elif 'General Information' in sheet.name:
            uid = sheet.row_values(i)[0]
            name_translated = sheet.row_values(i)[7]
            shortname_translated = sheet.row_values(i)[9]
            formname_translated = sheet.row_values(i)[3]
            description_translated = sheet.row_values(i)[5]
            type = sheet.row_values(i)[10].lower()
            if type == "program":
                program = api.get("/programs/" + uid + ".json?fields=*")
                program = insert_or_update_item(program, "NAME", name_translated)
                program = insert_or_update_item(program, "SHORT_NAME", shortname_translated)
                programs.append(program)
            elif type == "registration question":
                trackedentityattribute = api.get("/trackedEntityAttributes/" + uid + ".json?fields=*")
                trackedentityattribute = insert_or_update_item(trackedentityattribute, "DESCRIPTION", description_translated)
                trackedentityattribute = insert_or_update_item(trackedentityattribute, "FORM_NAME", formname_translated)
                trackedentityattribute = insert_or_update_item(trackedentityattribute, "NAME", formname_translated)
                trackedentityattribute = insert_or_update_item(trackedentityattribute, "SHORT_NAME", formname_translated)
                trackedentityattributes.append(trackedentityattribute)
            else:
                print(str(i)+"not found "+ uid)


with open('tranlations'+lang+'.json', 'w', encoding='utf-8') as outfile:
    json.dump({
        "options": options,
        "dataElements": dataelements,
        "trackedEntityAttributes": trackedentityattributes,
        "programs": programs,
        "programStages": programstages,
        "programStageSections": programstagesections
    }, outfile, ensure_ascii=False)