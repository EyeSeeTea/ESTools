import json
import sys

import requests

import dhis2api


def main():
    cfg = get_config("config.json")
    export_keep_data(cfg['server_config']['api_remote'], cfg['server_config']['local_temp_folder'], cfg['data'])
    import_keep_data(cfg['server_config']['api_local'], cfg['server_config']['local_temp_folder'], cfg['data'])


def get_config(fname):
    "Return dict with the options read from configuration file"
    print('Reading from config file %s ...' % fname)
    try:
        with open(fname) as f:
            config = json.load(f)
    except (AssertionError, IOError, ValueError) as e:
        sys.exit('Error reading config file %s: %s' % (fname, e))
    return config


def import_keep_data(cfg, folder, keep_data):
    for data in keep_data:
        if data['type'] == 'dataset':
            file = folder + "/" + data['dataset_uid']+data['ou_uid']+".json"
            response = import_data_set(cfg, file, data)
            return response


def remove_uids(json, uids):
    elements_new = []
    if 'dataValues' in json:
        for element in json['dataValues']:
            remove = remove_datalements(element, uids)
            if not remove:
                elements_new.append(element)
    return elements_new


def remove_datalements(element, removable_ids):
    if isinstance(element, list):
        for child in element[:]:
            if isinstance(child, dict) and "dataElement" in child.keys() and child["dataElement"] in removable_ids:
                return True
    elif isinstance(element, dict) and "dataElement" in element.keys() and element["dataElement"] in removable_ids:
        return True
    return False


def export_keep_data(api_local, folder, keep_data):
    for data in keep_data:
        if data['type'] == 'dataset':
            values = export_data_set(data['startdate'],data['enddate'], data['ou_uid'], data['dataset_uid'], api_local)
            if data['removeuids'] is not None:
                values =remove_uids(values, data['removeuids'])
            file = folder + "/" + data['dataset_uid']+data['ou_uid']+".json"

            with open(file, 'wt', encoding="utf-8") as fout:
                datavalues = json.dumps({"dataValues":values})
                fout.write(datavalues)


def export_data_set(start_date, end_date, ou_uid, dataset_uid, cfg):
    api = dhis2api.Dhis2Api(cfg['url'], cfg['username'], cfg['password'])

    wait_for_server(api)
    print('Exporting dataset: ou %s program %s' % (ou_uid, dataset_uid))

    if not dataset_uid or not ou_uid:
        print('No uid provided - Cancelling export dataset')
        return []

    post_content = 'dataElementIdScheme=UID&orgUnitIdScheme=UID&includeDeleted' \
                   '=false&children=true&categoryOptionComboIdScheme=CODE&start' \
                   'Date=%s&endDate=%s&orgUnit=%s&dataSet=%s' \
                   % (start_date, end_date, ou_uid, dataset_uid)

    response = api.get("/dataValueSets.json", post_content)

    return response


def import_data_set(cfg, file, data):
    print('Importing dataset: ou %s program %s' % (data['ou_uid'], data['dataset_uid']))

    api = dhis2api.Dhis2Api(cfg['url'], cfg['username'], cfg['password'])

    wait_for_server(api)

    file_to_import = json.load(open(file))
    response = api.post('/dataValueSets.json?dataElementIdScheme=UID&dryRun=false&idScheme=CODE' \
                   '&orgUnitIdScheme=UID&preheatCache=false&skipExistingCheck=false' \
                   '&strategy=NEW_AND_UPDATES&format=json&async=true', params={
    }, payload=file_to_import)

    if response.get('status') == 'OK':
        print(data['dataset_uid'] + "-" + data['ou_uid'] + ".json imported")
    else:
        print(data['dataset_uid'] + "-" + data['ou_uid'] + ".json failed")
    return response


def wait_for_server(api, delay=90, timeout=900):
    "Sleep until server is ready to accept requests"
    print('Check active API: %s' % api.api_url)
    import time
    time.sleep(delay)  # in case tomcat is still starting
    start_time = time.time()
    while True:
        try:
            api.get('/me')
            break
        except requests.exceptions.ConnectionError:
            if time.time() - start_time > timeout:
                raise RuntimeError('Timeout: could not connect to the API')
            time.sleep(1)


if __name__ == '__main__':
    main()