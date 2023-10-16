import json

from d2apy import dhis2api
from ipython_genutils.py3compat import xrange


def init_api(url, username, password):
    return dhis2api.Dhis2Api(url, username, password)

query_users_roles = "/users?fields=*&paging=false"
api = init_api("https://extranet.who.int/dhis2-cont-dev", "user", "pass")
widp_admins = ["sCjEPgiOhP1", "UfhhwZK73Lg"]
newUsers= {"users":[]}
id_filter = ""

users = api.get(query_users_roles)
for user in users["users"]:
    is_widp_admin_or_it = False
    for group in user["userGroups"]:
        if group["id"] in widp_admins:
            is_widp_admin_or_it = True
    if not is_widp_admin_or_it:
        user["userCredentials"]["disabled"] = True
        newUsers["users"].append(user)

print (users)

with open('user_disabled.json', 'w') as json_file:
    json.dump(newUsers, json_file,ensure_ascii=False)
