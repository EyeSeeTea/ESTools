#!/usr/bin/env python3

"""
Like cat on steroids to manipulate json files.

Its main utility is to read json data like the one produced by the
metadata export app in dhis2, and filter the different parts.

It can read json from a file (even if it's a zip file) or from stdin,
select a subset of sections, make string replacements, filter the
different parts (letting only elements in them whose selected field
matches the given regular expression), sort and compact the output.

A simple filter would look like:
  userGroups:name:HEP
which would select from the "userGroups" section only the elements that
have the letters "HEP" in some subfield called "name".

Instead of "HEP" one can use any regular expression, for example "^HEP"
if we want the name to start with "HEP", or "\.(dataentry|validator)$"
if we want it to end exactly with ".dataentry" or ".validator".

If instead of filtering sections we want to filter elements from
subsections, the filter will have as many ":" at the beginning as the
depth of the subsection. For example, to filter userGroupAccesses
(which may be inside a userGroup) and select only those with a
displayName that starts with HEP, the filter would look like:
  ::userGroupAccesses:displayName:^HEP

The filters can be either given with the --filters argument or read
from a file that contains one filter per line, with the --filters-file
argument.

It can be handy to manipulate metadata exported from dhis2, so it can
be imported in another instance.
"""
import copy
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter as fmt
import zipfile
import json
import subprocess

import requests

#CONFIG VARIABLES
user = ""
password = ""
start_id = 1000
output_teis = "teis.json"
output_enrollments = "enrollments.json"
url = "https://extranet.who.int/dhis2-demo/%s"
ou1 = "D5I2C9AX5Su"
ou1name = "ALERT Specialized Hospital"
ou2 = "Kskp6Epquur"
ou2name = "Dagemawi Minilik Hospital"
ou3 = "wC99G51EbUw"
ou3name = "St.Paul Hospital"

#GLOBAL VARIABLES
api_tei = "api/trackedEntityInstances/"
api_enrollments = "api/enrollments/"

tracker_entity_instance = {"trackedEntity":"vKBCptkP30X","trackedEntityInstance":"%s", "orgUnit":"H8RixfF8ugH","attributes":[{"attribute":"AAkZm4ZxFw7","value":"%s"},{"attribute":"KJiJQCbeZUm"},{"attribute":"PWEXwF166y5"},{"attribute":"pEXMTtqbjKU","value":"1"}]}
enrollment = {"trackedEntityInstance":"%s","enrollment":"%s", "program":"YGa3BmrwwiU","status":"ACTIVE","orgUnit":"H8RixfF8ugH","enrollmentDate":"2019-05-01","incidentDate":"2019-05-01"}

tracker_entity_instance_wrapper = {'trackedEntityInstances': []}
enrollment_wrapper = {'enrollments': []}


def main():
    args = get_args()

    text = create_fake_events(read(args.__getattribute__("input")[0]))

    write(args.output, text)


def get_args():
    "Parse command-line arguments and return them"
    global sort_fields, user, password

    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('input', nargs='*', help='input single or multiple files')

    add('-o', '--output', help='output file (write to stdout if not given')

    args = parser.parse_args()

    return args


def get_text_from_input(args):
    return read(args.input)


def read(fname):
    "Return contents of file, which works also for single zip files"
    if not fname:
        try:
            return sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(130)  # same as cat
    elif zipfile.is_zipfile(fname):
        zf = zipfile.ZipFile(fname)
        assert len(zf.filelist) == 1, \
            'Zip file "%s" should contain only one file' % fname
        with zf.open(zf.filelist[0], encoding="utf-8") as fin:
            return fin.read().decode('utf8')
    else:
        with open(fname, encoding="utf-8") as fin:
            return fin.read()


def read(fname):
    "Return contents of file, which works also for single zip files"
    if not fname:
        try:
            return sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(130)  # same as cat
    elif zipfile.is_zipfile(fname):
        zf = zipfile.ZipFile(fname)
        assert len(zf.filelist) == 1, \
            'Zip file "%s" should contain only one file' % fname
        with zf.open(zf.filelist[0], encoding="utf-8") as fin:
            return fin.read().decode('utf8')
    else:
        with open(fname, encoding="utf-8") as fin:
            return fin.read()


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


def create_fake_events(text):
    global start_id
    text = json.loads(text)
    for event in text:
        event.pop('coordinate', None)
        start_id = start_id+1
        print(start_id)
        print("tei")
        trackedEntityInstanceUID=get_code()
        print("enroll")
        enrollmentUID=get_code()
        if event['orgUnit'] is ou1:
            ou = ou2
            ouname = ou2name
        elif event['orgUnit'] is ou2:
            ou = ou1
            ouname = ou1name
        else:
            ou = ou3
            ouname = ou3name

        tracker_entity_instance_wrapper['trackedEntityInstances'].append(create_tracked_entity_instance(trackedEntityInstanceUID, start_id, ou))
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
    tei_json = json.dumps(tracker_entity_instance_wrapper, ensure_ascii=False)
    enrollments_json = json.dumps(enrollment_wrapper, ensure_ascii=False)
    post(tei_json, (url % api_tei))
    post(enrollments_json, (url % api_enrollments))
    write(output_teis, tei_json)
    write(output_enrollments, enrollments_json)
    return json.dumps(text, ensure_ascii=False)


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


def post(call, url):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=call, auth=(user, password))
    print(response)


if __name__ == '__main__':
    main()
