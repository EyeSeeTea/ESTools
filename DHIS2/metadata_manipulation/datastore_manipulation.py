"""This script replaces or merges all or a selected list of apps datastores."""

import json
from d2apy import dhis2api
from argparse import ArgumentParser, RawDescriptionHelpFormatter as fmt

strategies = ["merge", "replace"]
data_store_apps = "/dataStore"
api_query = "/dataStore/"


def init_api(url, username, password):
    return dhis2api.Dhis2Api(url, username, password)


def get_app_names(datastore_metadata, api, selected_apps):
    app_names = api.get(data_store_apps)
    for key in app_names:
        if selected_apps is None:
            datastore_metadata[key] = {}
        elif key in selected_apps:
            datastore_metadata[key] = {}
    return datastore_metadata


def get_data_store(datastore_metadata, api):
    for key in datastore_metadata:
        app_keys = api.get(data_store_apps + "/" + key)
        for app_key in app_keys:
            try:
                app_metadata = api.get(data_store_apps + "/" + key + "/" + app_key + "/metaData")
                datastore_metadata[key][app_key] = app_metadata
            # TODO: cleanup this exception
            except Exception:
                if not (key == "HMIS_Dictionary" and app_key == "test" or app_key == "test1"):
                    datastore_metadata[key][app_key] = {}
    return datastore_metadata


def delete_entire_app(destination_api, key):
    destination_api.delete(api_query + key)


def add_entire_app(destination_api, key, content):
    for item_key in content.keys():
        destination_api.post(api_query + key + "/" + item_key, json.loads(content[item_key]["value"]))


def add_app_key(destination_api, key, subkey, content):
    destination_api.post(api_query + key + "/" + subkey, json.loads(content["value"]))


def update_key(destination_api, key, subkey, content):
    if len(content["value"]) != 0:
        destination_api.put(api_query + key + "/" + subkey, json.loads(content["value"]))


def get_args():
    """Parse command-line arguments and return them"""
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('-a', '--apps', nargs='+', help='list of selected apps')
    add('-s', '--strategy', help='Strategy: merge or replace')
    add('-o', '--origin', help='Origin url')
    add('-ou', '--origin-user', help='Origin user')
    add('-op', '--origin-password', help='Origin password')
    add('-d', '--destination', help='destination url')
    add('-du', '--destination-user', help='destination user')
    add('-dp', '--destination-password', help='destination password')
    args = parser.parse_args()

    return args


def main():
    args = get_args()

    strategy = args.strategy
    selected_apps = args.apps
    origin_server = args.origin
    origin_user = args.origin_user
    origin_password = args.origin_password
    destination_server = args.destination
    destination_user = args.destination_user
    destination_password = args.destination_password
    print("Origin: " + origin_server)
    print("destination: " + destination_server)
    print("Strategy: " + strategy)
    if selected_apps is not None:
        print("Selected apps: " + ''.join(selected_apps))
    else:
        print("Selected apps: All")

    origin_datastore_metadata = {}
    destination_datastore_metadata = {}

    destination_api = init_api(destination_server, destination_user, destination_password)
    destination_datastore_metadata = get_app_names(destination_datastore_metadata, destination_api, selected_apps)
    destination_datastore_metadata = get_data_store(destination_datastore_metadata, destination_api)

    origin_api = init_api(origin_server, origin_user, origin_password)
    origin_datastore_metadata = get_app_names(origin_datastore_metadata, origin_api, selected_apps)
    new_datastore_metadata = dict(origin_datastore_metadata)
    origin_datastore_metadata = get_data_store(origin_datastore_metadata, origin_api)

    if strategy == "merge":
        for app_key in origin_datastore_metadata:
            mergeable = app_key not in destination_datastore_metadata.keys()
            # App key not exist in destination
            if mergeable:
                new_datastore_metadata[app_key] = origin_datastore_metadata[app_key]
                add_entire_app(destination_api, app_key, origin_datastore_metadata[app_key])
                continue
            else:
                for app_item_key_origin in origin_datastore_metadata[app_key].keys():
                    mergeable = app_item_key_origin not in destination_datastore_metadata[app_key].keys()
                    if mergeable:
                        # item-App key not exist in destination
                        new_datastore_metadata[app_key][app_item_key_origin] = origin_datastore_metadata[app_key][
                            app_item_key_origin]
                        add_app_key(destination_api, app_key, app_item_key_origin,
                                    origin_datastore_metadata[app_key][app_item_key_origin])
                        continue
                    else:
                        for app_item_key_destination in origin_datastore_metadata[app_key].keys():
                            if app_item_key_origin == app_item_key_destination:
                                # Hardcoded to merge the metadata-sync json lists
                                if app_key == "metadata-synchronization" and (
                                        app_item_key_destination == "rules" or app_item_key_destination == "history"):
                                    json_origin = json.loads(
                                        origin_datastore_metadata[app_key][app_item_key_origin]["value"])
                                    json_destination = json.loads(
                                        destination_datastore_metadata[app_key][app_item_key_destination]["value"])
                                    for json_origin_item in json_origin:
                                        exist = False
                                        for json_destination_item in json_destination:
                                            if json_destination_item["id"] == json_origin_item["id"]:
                                                exist = True
                                        if not exist:
                                            json_destination.append(json_origin_item)
                                    destination_datastore_metadata[app_key][app_item_key_origin]["value"] = json.dumps(
                                        json_destination)
                                    update_key(destination_api, app_key, app_item_key_origin,
                                               destination_datastore_metadata[app_key][app_item_key_origin])

                                if origin_datastore_metadata[app_key][app_item_key_origin]["lastUpdated"] > \
                                        destination_datastore_metadata[app_key][app_item_key_destination]["lastUpdated"]:
                                    new_datastore_metadata[app_key][app_item_key_origin] = \
                                        origin_datastore_metadata[app_key][app_item_key_origin]
                                    update_key(destination_api, app_key, app_item_key_origin,
                                               origin_datastore_metadata[app_key][app_item_key_origin])
                                    continue
    elif strategy == "replace":
        for app_key in origin_datastore_metadata:
            try:
                delete_entire_app(destination_api, app_key)
                add_entire_app(destination_api, app_key, origin_datastore_metadata[app_key])
            except Exception:
                print("Failing replacing " + app_key)

    # backup as .jsons
    with open('origin_datastore_metadata.json', 'w') as json_file:
        json.dump(origin_datastore_metadata, json_file, ensure_ascii=False)

    with open('destination_datastore_metadata.json', 'w') as json_file:
        json.dump(destination_datastore_metadata, json_file, ensure_ascii=False)

    with open('new_datastore_metadata.json', 'w') as json_file:
        json.dump(new_datastore_metadata, json_file, ensure_ascii=False)


if __name__ == '__main__':
    main()
