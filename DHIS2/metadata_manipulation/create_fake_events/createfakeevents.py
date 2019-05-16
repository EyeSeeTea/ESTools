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
import random
import time
from create_fake_events import dhis2api


#CONFIG VARIABLES
api = None
ous = ["seHJdofSPcM","D5I2C9AX5Su","wP2zKq0dDpw","EC9GQrjJG0M","Kskp6Epquur","yWc1CTszR3s","svSQSBLTVz6","zEYrsiNUGIo","H8RixfF8ugH","x9QBaHzG5aE","iWyyxvoa6DW","K5eT5a9sTZw","Ai4Wdk8hVps","fNZ3ZRjM8pK","zXAaAXzwt4M","fLhr5TrrZxw","spoX966fQm4","morX5MCo9PO","g3AzPbBKS44","NWjR36LLNjt","bcy4159FETR","rtLnlu4GUI2","YOL13ptz4ef","SnYHrnchKjL","afomkmfy9xk","Q2amTGc70TX","wC99G51EbUw","UN3mvCgeGVT","PHAPQ5aPRNx","tT99dpUmSaa","RA5zxsbittk","l5ionrzfp5t"]
ou_names = ["AFR","ALERT Specialized Hospital","AMR","CHU P-Zaga","Dagemawi Minilik Hospital","EMR","EUR","Federal Democratic Republic of Ethiopia","Global","Kawolo General Hospital","Lubaga Hospital","Masaka Regional Referral Hospital","Mengo Hospital","Mubende Regional Referral Hospital","NA","Naguru China Uganda Hospital","Nay Pyi Taw General Hospital","North Okkalapa General Hospital","Onandjokwe Hospital","Oshakati State Hospital","Republic of Madagascar","Republic of Namibia","Republic of the Union of Myanmar","Republic of Uganda","SEAR","St. Francis Hospital Nsambya","St.Paul Hospital","St.Peter Tuberculosis Specialized Hospital","Tikur Anbessa Specialized Hospital","Tirunesh Beijing Hospital","WPR","Yangon General Hospital"]

#GLOBAL VARIABLES
api_tei_endpoint = "/trackedEntityInstances"
api_enrollments_endpoint = "/enrollments"
api_events_endpoint = "/events"

tei_28_model = {"trackedEntity": "vKBCptkP30X", "trackedEntityInstance": "%s", "orgUnit": "H8RixfF8ugH", "attributes":[{"attribute": "AAkZm4ZxFw7", "value": "%s"}, {"attribute": "pEXMTtqbjKU", "value": "1"}]}
tei_30_model = {"trackedEntityType": "vKBCptkP30X", "trackedEntityInstance": "%s", "orgUnit": "H8RixfF8ugH", "attributes":[{"attribute": "AAkZm4ZxFw7", "value": "%s"}, {"attribute": "pEXMTtqbjKU", "value": "1"}]}
tei_models =  {}
tei_models['2.28'] = tei_28_model
tei_models['2.30'] = tei_30_model

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

    if not args.from_files:
        create_fake_events(json.load(open(args.input)), args.ETA_start_id, args.max_events, args.output_prefix, args.ETA_enrollment_start_date, args.ETA_enrollment_end_date, args.dhis2_version, args.seed_dhis2_version)

    if args.post:
        teis_json_payload = json.load(open("%s-teis.json" % args.output_prefix))
        enrollments_json_payload = json.load(open("%s-enrollments.json" % args.output_prefix))
        events_json_payload = json.load(open("%s-events.json" % args.output_prefix))

        api.post(api_tei_endpoint, payload=teis_json_payload)
        api.post(api_enrollments_endpoint, payload=enrollments_json_payload)
        api.post(api_events_endpoint, payload=events_json_payload)


def get_args():
    "Parse command-line arguments and return them"

    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut

    add('-i', '--input', help='input file')
    add('-o', '--output-prefix', help='output prefix for file name (write to stdout if not given')
    add('-s', '--server', default="https://extranet.who.int/dhis2-demo", help="server URL")
    add('-u', '--username', help='username for authentication')
    add('-p', '--password', help='password for authentication')
    add('-m', '--max-events', type=int, default=0,
        help='integer representing the max total number of events to be generated. events number will be min(m, number of events in events file)')
    add('-k', '--from-files', action='store_true', help='upload from previously-generated files')
    add('-l', '--post', action='store_true', default=False, help='whether to post json files to remove server')
    add('-t', '--ETA-start-id', type=int, default=1000, help='integer representing the ETA tracked entity attribute registry id')
    add('-f', '--ETA-enrollment-start-date', default="2018-01-01T12:00:00.000",
        help='date to be used as the start point to simulate enrollment dates')
    add('-e', '--ETA-enrollment-end-date', default="2019-05-01T12:00:00.000",
        help='date to be used as the end point to simulate enrollment dates')
    add('-d', '--dhis2-version', default="2.28", help='destination DHIS2 server version')
    add('-r', '--seed-dhis2-version', default="2.28", help='DHIS2 version for the events file used as seed')

    args = parser.parse_args()

    return args


def create_tracked_entity_instance(trackedEntityInstanceUID, id, ou, ouname, tei_position, extended, dhis2_version):
    #attribute UIDs
    ETA_attribute_register_id_UID = "AAkZm4ZxFw7"
    ETA_attribute_core_extended_UID = "pEXMTtqbjKU"
    ETA_attribute_gender_UID = "OkhvIL14Tbl"
    ETA_attribute_patient_residence_UID = "na3ZJRtjpGH"
    ETA_attribute_patient_ocupation_UID ="KJiJQCbeZUm"
    ETA_attribute_age_known_UID = "PWEXwF166y5"
    ETA_attribute_age_UID = "jOs4ColrsGt"

    #possible values
    patient_residence_values = ["1", "2", "77"]
    patient_ocupation_values = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "77", "88", "99"]

    new_tracker_entity_instance = copy.deepcopy(tei_models[dhis2_version])

    new_tracker_entity_instance['trackedEntityInstance'] = trackedEntityInstanceUID
    new_tracker_entity_instance['orgUnit'] = ou
    new_tracker_entity_instance['attributes'].append({'attribute': 'curur2uWaDy', 'value': ouname})

    for attribute in new_tracker_entity_instance['attributes']:
        if attribute['attribute'] is ETA_attribute_register_id_UID:
            attribute['value'] = id
        if attribute['attribute'] is ETA_attribute_core_extended_UID:
            attribute['value'] = "2" if extended else "1"

    if rand_percent(0.66):
        value = "M"
    else:
        value = "F"

    new_tracker_entity_instance['attributes'].append({"attribute": ETA_attribute_gender_UID, "value": value})

    if extended:
        #patient_residence
        index = tei_position % (len(patient_residence_values))
        new_tracker_entity_instance['attributes'].append({"attribute": ETA_attribute_patient_residence_UID, "value": patient_residence_values[index]})

        #patient_ocupation
        index = tei_position % (len(patient_ocupation_values))
        new_tracker_entity_instance['attributes'].append({"attribute": ETA_attribute_patient_ocupation_UID, "value": patient_ocupation_values[index]})

        #age
        value = (tei_position % 2) + 1
        age_known = rand_percent(0.5)
        new_tracker_entity_instance['attributes'].append({"attribute": ETA_attribute_age_known_UID, "value": "1" if age_known else "2"})
        new_tracker_entity_instance['attributes'].append({"attribute": ETA_attribute_age_UID, "value": random.randint(0, 100) if age_known else value})

    return new_tracker_entity_instance


def create_enrollment(trackedEntityInstanceUID, enrollmentUID, ou, enrollment_date):
    new_enrollment = copy.deepcopy(enrollment)
    new_enrollment['trackedEntityInstance'] = trackedEntityInstanceUID
    new_enrollment['enrollment'] = enrollmentUID
    new_enrollment['orgUnit'] = ou
    new_enrollment['incidentDate'] = enrollment_date
    new_enrollment['enrollmentDate'] = enrollment_date
    return new_enrollment


def gen_old_tei(events, max_events):
    id = 0
    old_tei_new_tei = dict()
    for event in events:
        if max_events > id:
            trackedEntityInstanceUID = get_code()
            if event['trackedEntityInstance'] not in old_tei_new_tei.keys():
                old_tei_new_tei.update({event['trackedEntityInstance']: trackedEntityInstanceUID})
        id = id + 1
    return old_tei_new_tei


def create_fake_events(events, ETA_start_id, max_events, output_prefix, start_date, end_date, dhis2_version, seed_dhis2_version):
    id = ETA_start_id
    events_wrapper = {}
    events_wrapper['events'] = []

    if max_events == 0:
        max_events = len(events['events'])
    old_tei_new_tei = gen_old_tei(events['events'], max_events)
    old_enr_new_enr = dict()
    gen_teis = list()
    for event in events['events']:
        if (max_events and max_events <= id-ETA_start_id):
            break

        enrollment_date = randomDate(start_date, end_date, random.random())
        event_date = randomDate(enrollment_date, end_date, random.random())

        event.pop('coordinate', None)
        eventUID = get_code()
        event['event'] = eventUID
        event['href'] = "%s/%s" % (event['href'].rsplit('/', 1)[0], eventUID)
        event['eventDate'] = event_date
        if dhis2_version == "2.30" and seed_dhis2_version == "2.28":
            event.pop('enrollmentStatus', None)
            event['status'] = "COMPLETED"
            event.pop('attributeOptionCombo', None)
            event.pop('attributeCategoryOptions', None)

        id+=1
        print("%s" % id)

        print("tei:")

        print("enrollment:")
        enrollmentUID = get_code()


        index = (id-ETA_start_id) % (len(ous)-1)
        ou = ous[index]
        ouname = ou_names[index]
        index += 1

        if id - ETA_start_id > int(len(old_tei_new_tei)/2):
            extended = True
        else:
            extended = False

        trackedEntityInstanceUID = old_tei_new_tei[event['trackedEntityInstance']]
        if trackedEntityInstanceUID not in gen_teis:
            gen_teis.append(trackedEntityInstanceUID)
            tracker_entity_instance_wrapper['trackedEntityInstances'].append(create_tracked_entity_instance(trackedEntityInstanceUID, id, ou, ouname, gen_teis.index(trackedEntityInstanceUID), extended, dhis2_version))

        if event['enrollment'] not in old_enr_new_enr.keys():
            old_enr_new_enr.update({event['enrollment']: enrollmentUID})
            enrollment_wrapper['enrollments'].append(create_enrollment(trackedEntityInstanceUID, enrollmentUID, ou, enrollment_date))

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

    tei_json = json.dumps(tracker_entity_instance_wrapper, ensure_ascii=False)
    enrollments_json = json.dumps(enrollment_wrapper, ensure_ascii=False)
    events_json = json.dumps(events_wrapper, ensure_ascii=False)

    write("%s-teis.json" % output_prefix if output_prefix else output_prefix, tei_json)
    write("%s-enrollments.json" % output_prefix if output_prefix else output_prefix, enrollments_json)
    write("%s-events.json" % output_prefix if output_prefix else output_prefix, events_json)

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


def rand_percent(percent):
    return random.random() < percent


def strTimeProp(start, end, format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def randomDate(start, end, prop):
    return strTimeProp(start, end, '%Y-%m-%dT%H:%M:%S.000', prop)


if __name__ == '__main__':
    main()
