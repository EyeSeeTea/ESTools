#!/usr/bin/env python3

"""
Get a description of a program.
"""

# The functions here are useful too in an interactive session, because
# we can use all the objects retrieved with get_object() without
# having to make any new query.

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import dhis2 as d2


def main():
    args = get_args()

    d2.USER = args.user
    d2.URLBASE = args.urlbase

    program = describe_program(args.program)
    if args.output:
        open(args.output, 'wt').write(program + '\n')
    else:
        print(program)


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('program', help='id of the program to describe')
    add('-o', '--output', help='output file')
    add('-u', '--user', metavar='USER:PASSWORD', required=True,
        help='username and password for server authentication')
    add('--urlbase', default='http://who-dev.essi.upc.edu:8081',
        help='base url of the dhis server')
    return parser.parse_args()


def describe_program(program_id):
    try:
        program = d2.get_object(program_id)
        name = program['name']
        attribute_ids = [x['trackedEntityAttribute']['id'] for x in
                         program['programTrackedEntityAttributes']]
        attributes = describe_attributes(attribute_ids)
        stages = describe_stages(id_list(program['programStages']))
        rules = describe_rules(id_list(program['programRules']))
        variables = describe_variables(id_list(program['programRuleVariables']))
        return """%s (%s)

Attributes
  %s

Stages - Sections - Dataelements
  %s

Rules (name: condition --> action)
  %s

Variables
  %s""" % (name, program_id,
           attributes.replace('\n', '\n  '),
           stages.replace('\n', '\n  '),
           rules.replace('\n', '\n  '),
           variables.replace('\n', '\n  '))
    except KeyError:
        return '***%s***' % program_id  # could not find it


def id_list(a):  # we often get lists like [{'id': 'xxxx'}, {'id': 'yyyy'}, ...]
    return [x['id'] for x in a]


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



if __name__ == '__main__':
    main()
