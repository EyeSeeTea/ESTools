import json
import csv
import requests
from requests.auth import HTTPBasicAuth

server = 'http://localhost:8080/api/userRoles/{}.json'
serverusername = ''
password = ''
def get_names_by_id(uid, server, user, password):
    url = server.format(uid)
    payload = {}
    response = requests.request("GET", url, data=payload, auth=HTTPBasicAuth(user,password))

    if response.status_code == 200:
        name = response.json().get('name')
        return name
    else:
        return "name not found"


# Load the JSON files
with open('users1.json', 'r') as file:
    data1 = json.load(file)
with open('users2.json', 'r') as file:
    data2 = json.load(file)

# Adjusted the variable assignments here according to your later clarification
users1 = {user['username']: user for user in data2}
users2 = {user['username']: user for user in data1}

differences = []


for username, user in users1.items():
    if username in users2:
        ids1 = {role['id'] for role in user.get('userRoles', [])}
        ids2 = {role['id'] for role in users2[username].get('userRoles', [])}

        diff_ids = ids1.difference(ids2)

        if diff_ids:
            names = [get_names_by_id(uid, server, serverusername, password) for uid in diff_ids]
            differences.append({
                'username': username,
                'missing_ids_in_json2': ', '.join(diff_ids),
                'names': ', '.join(names)
            })

for username, user in users2.items():
    if username not in users1:
        ids2 = {role['id'] for role in user.get('userRoles', [])}
        differences.append({'username': username, 'missing_ids_in_json2': ', '.join(ids2), 'names': 'N/A'})

with open('differences.csv', 'w', newline='') as file:
    fieldnames = ['username', 'missing_ids_in_json2', "names"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in differences:
        writer.writerow(row)

print("The CSV file with the differences has been created.")
