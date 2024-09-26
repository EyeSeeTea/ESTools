#!/usr/bin/env python3

"""
Get a description of a program.
"""

# The functions here are useful too in an interactive session, because
# we can use all the objects retrieved with get_object() without
# having to make any new query.
import json
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
import DHIS2.metadata_manipulation.dhis2 as d2
from DHIS2.metadata_manipulation.common.common import get_code

api_program_rules_query = "programRules.json?fields=id,program&paging=false"
api_indicators_query = "indicators?filter=name:$like:ETA&fields=[id,name,numerator,denominator]&paging=false"
program_indicator = "programIndicators"
program_stage = "programStages"
program_rule = "programRules"
indicator = "indicators"
tracked_entity_attribute = "trackedEntityAttribute"


def main():
    args = get_args()

    d2.USER = args.user
    d2.URLBASE = args.urlbase

    csv = read_csv(args.input)
    if args.action == "describe":
        replace = False
    elif args.action == "replace":
        replace = True
    if args.type == "text":
        to_json = False
    elif args.type == "json":
        to_json = True
    if args.strategy == "all":
        uid_list = list()
    elif args.strategy == "only_referenced":
        uid_list = get_uids(csv)
        # get list from csv
    # get mapping hasmap from csv
    program = describe_program(args.program, args.objects, replace, uid_list, csv, args.type, to_json)
    if args.output:
        program = program + '\n'
        open(args.output, 'wt').write(program)
    else:
        print(program)


def read_csv(input_file):
    result = list()
    if input_file is None:
        return result
    import csv
    count = 0
    with open(input_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            count = count + 1
            if count > 1:
                result.append({"type": row[0], "uid_old":row[3], "uid_new": row[4]})
    return result


def get_uids(csv):
    result = list()
    for item in csv:
        result.append(item['uid_old'])
    return result


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('program', help='id of the program to describe')
    add('-o', '--output', help='output file')
    add('-i', '--input', help='input file')
    add('-a', '--action', help='action(describe/replace) default: describe', default="describe")
    add('-t', '--type', help='output type (json/text) default: text', default="text")
    add('-s', '--strategy', help='strategy (only_referenced/all) default: only_referenced', default="only_referenced")
    add('-ob', '--objects', nargs='*',
        help='Objects (indicators/programRules/programIndicators/trackedEntityAttribute/programStages/all) '
             'default: indicators programIndicators', default="indicators programIndicators")
    add('-u', '--user', metavar='USER:PASSWORD', required=True,
        help='username and password for server authentication')
    add('--urlbase', default='https://extranet-uat.who.int/dhis2',
        help='base url of the dhis server')
    return parser.parse_args()


def describe_program(program_id, objects, replace, uid_list, mapping_list, type, to_json):
    try:
        program = d2.get_object(program_id)
        name = program['name']
        #TODO: implement replace and text/to_json for programstages, programrules and trackedentityattributes
        attributes = ""
        if tracked_entity_attribute in objects:
            attributes = describe_attributes(
                [x['trackedEntityAttribute']['id'] for x in program['programTrackedEntityAttributes']])

        program_indicators = ""
        if program_indicator in objects:
            program_indicators = describe_program_indicators(id_list(program[program_indicator]), uid_list, replace, to_json)

        program_stages = ""
        if program_stage in objects:
            program_stages = describe_stages(id_list(program[program_stage]))

        program_rules = ""
        program_rule_variables = ""
        if program_rule in objects:
            program_rules = describe_rules(get_program_rules(program_id))
            program_rule_variables = describe_variables(id_list(program['programRuleVariables']))

        indicators = ""
        if indicator in objects:
            indicators = describe_indicators(get_indicators(replace), uid_list, replace, to_json)

        if type == "text":
            output = format_as_text(name, program_id, attributes, program_stages, program_rules, program_rule_variables, program_indicators,
                                    indicators)
        elif type == "json":
            output = format_as_json(attributes, program_stages, program_rules, program_rule_variables, program_indicators,
                                    indicators)

        if replace:
            return replace_output(output, mapping_list)
        else:
            return output

    except KeyError:
        return '***%s***' % program_id  # could not find it


def format_as_text(name, program_id, attributes, stages, rules, variables, program_indicators, indicators):
    return """%s (%s)

Attributes
  %s

Stages - Sections - Dataelements
  %s

Rules (name: condition --> action)
  %s

Variables
  %s
    
Program Indicators
  %s
    
Indicators
  %s""" % (name, program_id,
           attributes.replace('\n', '\n  '),
           stages.replace('\n', '\n  '),
           rules.replace('\n', '\n  '),
           variables.replace('\n', '\n  '),
           program_indicators.replace('\n', '\n  '),
           indicators.replace('\n', '\n  '))


def format_as_json(attributes, stages, rules, variables, program_indicators, indicators):
    return """{"trackedEntityAttributes":[%s], "programStages":[%s], "programRules":[%s], "programRuleVariables":[%s],
     "programIndicators":[%s], "indicators":[%s]}""" % (
           attributes,
           stages,
           rules,
           variables,
           program_indicators,
           indicators)


def replace_output(output, mapping_list):
    for item in mapping_list:
        if item["type"] == "attribute":
            output = output.replace("A{"+item["uid_old"]+"}", "#{"+item["uid_new"]+"}")
        output = output.replace(item["uid_old"], item["uid_new"])
    return output


def id_list(a):  # we often get lists like [{'id': 'xxxx'}, {'id': 'yyyy'}, ...]
    return [x['id'] for x in a]


def get_program_rules(program_id):
    program_program_rules = list()
    all_program_rules = d2.get(api_program_rules_query)
    for program_rule in all_program_rules["programRules"]:
        if program_rule['program']['id'] == program_id:
            program_program_rules.append(program_rule['id'])
    return program_program_rules


def get_indicators(replace):
    indicators = list()
    all_indicators = d2.get(api_indicators_query)
    for indicator in all_indicators["indicators"]:
        if replace:
            indicator["old_id"] = (indicator["id"])
            indicator["id"] = get_code()
        indicators.append(indicator)
    return indicators


def describe_indicators(program_indicators, uid_list, replace, to_json):
    if to_json:
        indicator_list = list()
        for x in program_indicators:
            indicator_list.append(describe_indicator(x, uid_list, replace, to_json))
        return json.dumps(indicator_list)
    else:
        return '\n'.join(describe_indicator(x, uid_list, replace, to_json) for x in program_indicators)


def describe_indicator(var, uid_list, replace, to_json):
    try:
        if should_be_copied(json.dumps(var), uid_list):
            if replace:
                var["old_id"] = var["id"]
                var["id"] = get_code()
            if to_json:
                return var
            else:
                name = indicator['name']
                numerator = "numerator: " + indicator['numerator']
                denominator = "denominator: " + indicator['denominator']
                id = indicator['id']
                return """%s (%s):
          %s -->
            %s""" % (name, id, numerator, denominator)
                return '%s (%s)' % (name, id)
    except KeyError:
        return '***%s***' % indicator  # could not find it


def describe_attributes(attributes):
    return '\n'.join(describe_attribute(x) for x in attributes)


def describe_attribute(attribute_id):
    try:
        attribute = d2.get_object(attribute_id)
        name = attribute['name']
        return '%s (%s)' % (name, attribute_id)
    except KeyError:
        return '***%s***' % attribute_id  # could not find it


def describe_stages(stages):
    return '\n'.join(describe_stage(x) for x in stages)


def describe_stage(stage_id):
    try:
        stage = d2.get_object(stage_id)
        name = stage['name']
        stype = stage['formType']
        if stype == 'SECTION':
            extra = describe_sections(id_list(stage['programStageSections']))
        else:
            dataelements_ids = [x['dataElement']['id'] for x in
                                stage['programStageDataElements']]
            extra = describe_dataelements(dataelements_ids)
        return """%s (%s) (type %s)
  %s""" % (name, stage_id, stype, extra.replace('\n', '\n  '))
    except KeyError:
        return '***%s***' % stage_id  # could not find it


def describe_sections(sections):
    return '\n'.join(describe_section(x) for x in sections)


def describe_section(section_id):
    try:
        section = d2.get_object(section_id)
        name = section['name']
        dataelements = describe_dataelements(id_list(section['dataElements']))
        return """%s (%s)
  %s""" % (name, section_id,
           dataelements.replace('\n', '\n  '))
    except KeyError:
        return '***%s***' % section_id  # could not find it


def describe_dataelements(dataelements):
    return '\n'.join(describe_dataelement(x) for x in dataelements)


def describe_dataelement(dataelement_id):
    try:
        dataelement = d2.get_object(dataelement_id)
        name = dataelement['name']
        return '%s (%s)' % (name, dataelement_id)
    except KeyError:
        return '***%s***' % dataelement_id  # could not find it


def describe_rules(rules):
    return '\n'.join(describe_rule(x) for x in rules)


def describe_rule(rule_id):
    try:
        rule = d2.get_object(rule_id)
        name = rule['name']
        condition = rule['condition']
        actions = describe_actions(id_list(rule['programRuleActions']))
        return """%s (%s):
  %s -->
    %s""" % (name, rule_id, condition,
             actions.replace('\n', '\n    '))
    except KeyError:
        return '***%s***' % rule_id  # could not find it


def describe_actions(actions):
    return '\n'.join(describe_action(x) for x in actions)


def describe_action(action_id):
    try:
        action = d2.get_object(action_id)
        atype = action['programRuleActionType']
        extra = ''
        if 'dataElement' in action:
            extra += ' elem:"%s"' % describe_dataelement(
                action['dataElement']['id'])
        if 'trackedEntityAttribute' in action:
            extra += ' attr:"%s"' % describe_trackedentityattribute(
                action['trackedEntityAttribute']['id'])
        if 'programStage' in action:
            sid = action['programStage']['id']
            extra += ' stage:"%s (%s)"' % (d2.get_object(sid)['name'], sid)
        if 'programStageSection' in action:
            sid = action['programStageSection']['id']
            extra += ' sect:"%s (%s)"' % (d2.get_object(sid)['name'], sid)
        if 'data' in action:
            extra += ' data:"%s"' % action['data']
        return '%s (%s)%s' % (atype, action_id, extra)
    except KeyError:
        return '***%s***' % action_id  # could not find it


def describe_trackedentityattribute(attr_id):
    try:
        attr = d2.get_object(attr_id)
        name = attr['name']
        return '%s (%s)' % (name, attr_id)
    except KeyError:
        return '***%s***' % attr_id  # could not find it


def describe_variables(variables):
    return '\n'.join(describe_variable(x) for x in variables)


def describe_variable(variable_id):
    try:
        var = d2.get_object(variable_id)
        name = var['name']
        extra = ''
        if 'dataElement' in var:
            extra += ' elem:"%s"' % describe_dataelement(
                var['dataElement']['id'])
        if 'trackedEntityAttribute' in var:
            extra += ' attr:"%s"' % describe_trackedentityattribute(
                var['trackedEntityAttribute']['id'])
        return '%s (%s) -->%s' % (name, variable_id, extra)
    except KeyError:
        return '***%s***' % variable_id  # could not find it


def describe_program_indicators(program_indicators, uid_list, replace, to_json):
    if to_json:
        program_indicator_list = list()
        for x in program_indicators:
            program_indicator_list.append(describe_program_indicator(x, uid_list, replace, to_json))
        return json.dumps(program_indicator_list)
    else:
        return '\n'.join(describe_program_indicator(x, uid_list, replace, to_json) for x in program_indicators)


def should_be_copied(object, uid_list):
    is_valid = False
    if len(uid_list) == 0:
        return is_valid
    for uid in uid_list:
        if uid in object:
            is_valid = True
            break
    return is_valid


def describe_program_indicator(program_indicator_id, uid_list, replace, to_json):
    try:
        var = d2.get_object(program_indicator_id)
        if should_be_copied(json.dumps(var), uid_list):
            if True:
                if replace:
                    var["name"] = var["name"] + "(events)"
                    var["shortName"] = var["shortName"][0:48] + "_E"
                    if "code" in var.keys():
                        var["code"] = var["code"] + "(events)"
                    if "analyticsPeriodBoundaries" in var.keys():
                        for x in var["analyticsPeriodBoundaries"]:
                            x["id"] = get_code()
                    var["old_id"] = var["id"]
                    var["id"] = get_code()
                if to_json:
                    return var
                else:
                    name = var['name']
                    extra = ""
                    if 'expression' in var.keys():
                        extra = '\n expression: %s' % var['expression']
                    if 'filter' in var.keys():
                        extra += '\n filter: %s' % var['filter']
                    return '%s (%s) -->%s' % (name, program_indicator_id, extra)
        else:
            return ""
    except KeyError:
        return '***%s***' % program_indicator_id  # could not find it

if __name__ == '__main__':
    main()
