import json
import csv
import os
from os import listdir
from os.path import isfile, join
input_folder = "input"
output_folder = "output"
is_json = lambda fname: os.path.splitext(fname)[-1] in ['.json']
is_not_json = lambda fname: not os.path.splitext(fname)[-1] in ['.json']
is_not_git = lambda fname: not fname.startswith(".git")
applied_filter = is_not_git if is_json else is_not_json

files = [f for f in filter(applied_filter, listdir(input_folder)) if isfile(join(input_folder, f))]
for path_file in files:
    with open(join(output_folder, path_file).replace(".json","")+".csv", mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        with open(join(output_folder, path_file).replace(".json","_errors")+".csv", mode='w') as csv_file_errors:
            csv_writer_errors = csv.writer(csv_file_errors, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            print(path_file)
            with open(join(input_folder, path_file)) as json_file:
                data = json.load(json_file)
                count = 0
                for rule in data["messages"]:
                    if count == 0:
                        csv_writer.writerow(['-----------------------------------------------'])
                        csv_writer.writerow(['imported', 'updated', 'ignored', 'total'])
                    imported = rule["stats"]["imported"]
                    updated = rule["stats"]["updated"]
                    ignored = rule["stats"]["ignored"]
                    total = rule["stats"]["imported"] + rule["stats"]["updated"] + rule["stats"]["ignored"]
                    csv_writer.writerow([imported, updated, ignored, total])

                    if count == 0:
                        csv_writer_errors.writerow(['uid', 'message', "", ""])
                    for messages in rule["report"]["messages"]:
                        if "uid" in messages.keys():
                            uid = messages["uid"]
                        else:
                            uid = None
                        message = messages["message"]
                        csv_writer_errors.writerow([uid, message, "", ""])
                    count = count +1