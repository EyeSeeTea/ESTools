import json

from d2apy import dhis2api
from ipython_genutils.py3compat import xrange


def init_api(url, username, password):
    return dhis2api.Dhis2Api(url, username, password)
query_old_roles = "/userRoles.json?filter=name:$like:_old_&paging=false&fields=id"
query_users_roles = "/users?filter=userCredentials.userRoles.id:in:[%s]&fields=*&paging=false"
api = init_api("https://..", "user", "pass")

userRoles = api.get(query_old_roles)
id_filter = ""
for role in userRoles["userRoles"]:
    id_filter = id_filter + role["id"]+","
users = api.get((query_users_roles % id_filter).replace(",]","]"))
for user in users["users"]:
    usercreed = user['userCredentials']

    new_list = []
    for i in xrange(len(usercreed["userRoles"])):
        is_old_role = False
        if (usercreed["userRoles"][i]["id"] in id_filter):
            is_old_role = True
        if not is_old_role:
            new_list.append(usercreed["userRoles"][i])
    usercreed["userRoles"] = new_list

print (users)

with open('user_result.json', 'w') as json_file:
    json.dump(users, json_file,ensure_ascii=False)


