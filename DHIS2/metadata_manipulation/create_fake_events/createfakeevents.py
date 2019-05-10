#!/usr/bin/env python3

"""
Handy script to generate a set of events and upload them to a given server.

You can choose to upload them or to generate a couple of json files to be imported
"""
import copy
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter as fmt
import json
import subprocess
from create_fake_events import dhis2api

import requests

#CONFIG VARIABLES
api = None
user = ""
password = ""

ou1 = "D5I2C9AX5Su"
ou1name = "ALERT Specialized Hospital"
ou2 = "Kskp6Epquur"
ou2name = "Dagemawi Minilik Hospital"
ou3 = "wC99G51EbUw"
ou3name = "St.Paul Hospital"
ous = [ou1, ou2]
ou_names = [ou1name, ou2name]
default_ou = ou3
default_ouname = ou3name

#GLOBAL VARIABLES
api_tei_endpoint = "/trackedEntityInstances"
api_enrollments_endpoint = "/enrollments"
api_events_endpoint = "/events"

tracker_entity_instance = {"trackedEntity":"vKBCptkP30X","trackedEntityInstance":"%s", "orgUnit":"H8RixfF8ugH","attributes":[{"attribute":"AAkZm4ZxFw7","value":"%s"},{"attribute":"KJiJQCbeZUm"},{"attribute":"PWEXwF166y5"},{"attribute":"pEXMTtqbjKU","value":"1"}]}
enrollment = {"trackedEntityInstance":"%s","enrollment":"%s", "program":"YGa3BmrwwiU","status":"ACTIVE","orgUnit":"H8RixfF8ugH","enrollmentDate":"2019-05-01","incidentDate":"2019-05-01"}

tracker_entity_instance_wrapper = {'trackedEntityInstances': []}
enrollment_wrapper = {'enrollments': []}


def main():
    global api
    args = get_args()

    if args.post and (not args.username or not args.password or not args.server):
        print("ERROR: Please provide server, username and password")
        sys.exit()

    api = dhis2api.Dhis2Api(args.server, args.username, args.password)

    create_fake_events(json.load(open(args.input)), args.ETA_start_id, args.max_events, args.output_prefix, args.post, args.from_files)


def get_args():
    "Parse command-line arguments and return them"

    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut

    add('-i', '--input', help='input file')
    add('-o', '--output-prefix', help='output prefix for file name (write to stdout if not given')
    add('-s', '--server', default="https://extranet.who.int/dhis2-demo", help="server URL")
    add('-u', '--username', help='username for authentication')
    add('-p', '--password', help='password for authentication')
    add('-m', '--max-events', type=int,
        help='integer representing the max total number of events to be generated. events number will be min(m, number of events in events file)')
    add('-k', '--from-files', action='store_true', help='upload from previously-generated files')
    add('-l', '--post', action='store_true', default=False, help='whether to post json files to remove server')
    add('-t', '--ETA-start-id', type=int, default=1000, help='integer representing the ETA tracked entity attribute registry id')

    args = parser.parse_args()

    return args


def create_tracked_entity_instance(trackedEntityInstanceUID, id, ou):
    new_tracker_entity_instance = copy.deepcopy(tracker_entity_instance)

    new_tracker_entity_instance['trackedEntityInstance'] = trackedEntityInstanceUID
    new_tracker_entity_instance['orgUnit'] = ou
    for attribute in new_tracker_entity_instance['attributes']:
        if attribute['attribute'] is "AAkZm4ZxFw7":
            attribute['value'] = id
    return new_tracker_entity_instance


def create_enrollment(trackedEntityInstanceUID, enrollmentUID, ou):
    new_enrollment = copy.deepcopy(enrollment)
    new_enrollment['trackedEntityInstance'] = trackedEntityInstanceUID
    new_enrollment['enrollment'] = enrollmentUID
    new_enrollment['orgUnit'] = ou
    return new_enrollment


def create_fake_events(events, ETA_start_id, max_events, output_prefix, post, from_files):
    id = ETA_start_id
    events_wrapper = {}
    events_wrapper['events'] = []

    for event in events['events']:
        if (max_events and max_events <= id-ETA_start_id) or from_files:
            break
        event.pop('coordinate', None)
        eventUID = get_code()
        event['event'] = eventUID
        event['href'] = "%s/%s" % (event['href'].rsplit('/', 1)[0], eventUID)

        id+=1
        print("%s" % id)

        print("tei:")
        trackedEntityInstanceUID = get_code()

        print("enrollment:")
        enrollmentUID = get_code()

        if event['orgUnit'] in ous:
            index = ous.index(event['orgUnit'])
            index +=1
            if index == len(ous):
                index = 0
            ou = ous[index]
            ouname = ou_names[index]
        else:
            ou = default_ou
            ouname = default_ouname

        tracker_entity_instance_wrapper['trackedEntityInstances'].append(create_tracked_entity_instance(trackedEntityInstanceUID, id, ou))
        enrollment_wrapper['enrollments'].append(create_enrollment(trackedEntityInstanceUID, enrollmentUID, ou))
        for key in event:
            value = event[key]

            if isinstance(event[key], dict):
                event[key] = [event[key], value]
            if key == "orgUnit":
                event[key] = ou
            if key == "orgUnitName":
                event[key] = ouname
            if key == "trackedEntityInstance":
                event[key] = trackedEntityInstanceUID
            if key == "enrollment":
                event[key] = enrollmentUID
        events_wrapper['events'].append(event)

    if not from_files:
        tei_json = json.dumps(tracker_entity_instance_wrapper, ensure_ascii=False)
        enrollments_json = json.dumps(enrollment_wrapper, ensure_ascii=False)
        events_json = json.dumps(events_wrapper, ensure_ascii=False)

        write("%s-teis.json" % output_prefix if output_prefix else output_prefix, tei_json)
        write("%s-enrollments.json" % output_prefix if output_prefix else output_prefix, enrollments_json)
        write("%s-events.json" % output_prefix if output_prefix else output_prefix, events_json)

    if post:
        teis_json_payload = json.load(open("%s-teis.json" % output_prefix))
        enrollments_json_payload = json.load(open("%s-enrollments.json" % output_prefix))
        events_json_payload = json.load(open("%s-events.json" % output_prefix))

        api.post(api_tei_endpoint, payload=teis_json_payload)
        api.post(api_enrollments_endpoint, payload=enrollments_json_payload)
        api.post(api_events_endpoint, payload=events_json_payload)

    return


def write(fname, text):
    if fname:
        with open(fname, 'wt', encoding="utf-8") as fout:
            fout.write(text)
    else:
        print(text, end='')


def remove_field(text, field):
    "Removed all the appearances of the given field in text"
    text_filtered = ''
    in_field = False
    for line in text.splitlines():
        line_stripped = line.lstrip()
        if not in_field:
            if line_stripped.startswith('"%s":' % field):
                indent = len(line) - len(line.lstrip())
                in_field = True
            else:
                text_filtered += line + '\n'
        else:
            if len(line) - len(line_stripped) <= indent:
                in_field = False
                if (len(line) - len(line_stripped) < indent or
                    line_stripped[0] not in ['}', ']']):
                    text_filtered += line + '\n'
    return text_filtered


def get_code():
    command = "java CodeGenerator"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print(output)
    return str(output).replace("b'", "").replace("\\n'", "")


if __name__ == '__main__':
    main()
