import csv

import json
lang="pt"

def get_translation(type, translations, lang):
    if len(translations)>1:
        for translation in translations:
            if type == translation["property"] and lang == translation["locale"]:
                return translation["value"]
    return ""


def init(lang):
    with open('paho.json') as json_file:
        data = json.load(json_file)
        with open(lang+'tea.csv', mode='w') as employee_file:
            employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            employee_writer.writerow(
                ['UID', 'Variable name', 'Form name', 'Form name (translation)', 'Description', 'Description (translation)',
                 'name', 'name (translation)', 'shortName', 'shortName (translation)', 'type'])
            for p in data['trackedEntityAttributes']:
                form_name=""
                description=""
                name=""
                shortName=""
                code = ""
                if "description" in p.keys():
                    description = p["description"]
                if "formName" in p.keys():
                    form_name = p["formName"]
                if "name" in p.keys():
                    name = p["name"]
                if "shortName" in p.keys():
                    shortName = p["shortName"]
                if "code" in p.keys():
                    code = p["code"]
                employee_writer.writerow([p["id"], code, form_name, get_translation("FORM_NAME", p["translations"], lang),
                                          description, get_translation("DESCRIPTION", p["translations"], lang),
                                          name, get_translation("NAME", p["translations"], lang),
                                          shortName, get_translation("SHORT_NAME", p["translations"], lang),
                                          'Registration question'])

        with open(lang+'options.csv', mode='w') as employee_file:
            employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            employee_writer.writerow(
                ['UID', 'Variable name', 'Optionset', 'Option name', 'Name (translation)'])
            for p in data['options']:
                name=""
                code = ""
                if "name" in p.keys():
                    name = p["name"]
                if "code" in p.keys():
                    code = p["code"]
                employee_writer.writerow([p["id"], code, p["optionSet"]["id"],
                                          name, get_translation("NAME", p["translations"], lang)])
        with open(lang+'dataElements.csv', mode='w') as employee_file:
            employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            employee_writer.writerow(
                ['UID', 'Variable name', 'type', 'name', 'name (translation)', 'shortName', 'shortName (translation)',
                 'Form name', 'Form name (translation)', 'Description', 'Description (translation)',
                 "Data Type", "Optionset"
                 ])
            for p in data['dataElements']:
                form_name=""
                description=""
                name=""
                shortName=""
                code = ""
                if "description" in p.keys():
                    description = p["description"]
                if "formName" in p.keys():
                    form_name = p["formName"]
                if "name" in p.keys():
                    name = p["name"]
                if "shortName" in p.keys():
                    shortName = p["shortName"]
                if "code" in p.keys():
                    code = p["code"]
                optionset = ""
                if "optionSet" in p.keys():
                    optionset = p["optionSet"]["id"]
                employee_writer.writerow([p["id"], code, "Question",
                                          name, get_translation("NAME", p["translations"], lang),
                                          shortName, get_translation("SHORT_NAME", p["translations"], lang),
                                          form_name, get_translation("FORM_NAME", p["translations"], lang),
                                          description, get_translation("DESCRIPTION", p["translations"], lang),
                                         p["valueType"], optionset])
        with open(lang+'info.csv', mode='w') as employee_file:
            employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            employee_writer.writerow(
                ['UID', 'Variable name', 'Form name', 'Form name (translation)',
                  'Description', 'Description (translation)',
                 'name', 'name (translation)', 'shortName', 'shortName (translation)',
                 'type'
                 ])
            for p in data['programStages']:
                form_name=""
                description=""
                name=""
                shortName=""
                code = ""
                if "description" in p.keys():
                    description = p["description"]
                if "formName" in p.keys():
                    form_name = p["formName"]
                if "name" in p.keys():
                    name = p["name"]
                if "shortName" in p.keys():
                    shortName = p["shortName"]
                if "code" in p.keys():
                    code = p["code"]
                employee_writer.writerow([p["id"], code,
                                          form_name, get_translation("FORM_NAME", p["translations"], lang),
                                          description, get_translation("DESCRIPTION", p["translations"], lang),
                                          name, get_translation("NAME", p["translations"], lang),
                                          shortName, get_translation("SHORT_NAME", p["translations"], lang),
                                          "form"])

        with open(lang+'infosections.csv', mode='w') as employee_file:
            employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            employee_writer.writerow(
                ['UID', 'Variable name', 'Form name', 'Form name (translation)',
                  'Description', 'Description (translation)',
                 'name', 'name (translation)', 'shortName', 'shortName (translation)',
                 'type'
                 ])
            for p in data['programStageSections']:
                form_name=""
                description=""
                name=""
                shortName=""
                code = ""
                if "description" in p.keys():
                    description = p["description"]
                if "formName" in p.keys():
                    form_name = p["formName"]
                if "name" in p.keys():
                    name = p["name"]
                if "shortName" in p.keys():
                    shortName = p["shortName"]
                if "code" in p.keys():
                    code = p["code"]
                employee_writer.writerow([p["id"], code,
                                          form_name, get_translation("FORM_NAME", p["translations"], lang),
                                          description, get_translation("DESCRIPTION", p["translations"], lang),
                                          name, get_translation("NAME", p["translations"], lang),
                                          shortName, get_translation("SHORT_NAME", p["translations"], lang),
                                          "section"])
init("pt")
init("nl")