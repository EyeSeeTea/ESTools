import json
import csv

output_file = 'result_messages.csv'
#the notification list is a list of notifications with format [ {notification}, {notification }], I have to remove the [] of the notification stored in the data datastore
notification_list_json ='/home/idelcano/conversion_script/WHO-scripts/dhis2godata/input/ANNEX_EMRO_EN.json'

with open(output_file, mode='w') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    with open(notification_list_json) as json_file:
        data = json.load(json_file)
        for rule in data["messages"]:
            csv_writer.writerow(['-----------------------------------------------'])
            csv_writer.writerow(['imported', 'updated', 'ignored', 'total'])
            imported = rule["stats"]["imported"]
            updated = rule["stats"]["updated"]
            ignored = rule["stats"]["ignored"]
            total = rule["stats"]["imported"] + rule["stats"]["updated"] + rule["stats"]["ignored"]
            csv_writer.writerow([imported, updated, ignored, total])
            csv_writer.writerow(['uid', 'message', "", ""])
            for messages in rule["report"]["messages"]:
                if "uid" in messages.keys():
                    uid = messages["uid"]
                else:
                    uid = None
                message = messages["message"]
                csv_writer.writerow([uid, message, "", ""])