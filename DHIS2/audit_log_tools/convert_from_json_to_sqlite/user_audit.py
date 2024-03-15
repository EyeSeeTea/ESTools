import json

from usergroup_audit import UserGroupAudit


class UserAudit:
    def __init__(self):
        self.uid = ""
        self.lastLogin = ""
        self.lastUpdated = ""
        self.open_id = ""
        self.created = ""
        self.user_roles = ""
        self.user_roles_count = ""
        self.created_by = ""
        self.surname = ""
        self.firstname = ""
        self.disabled = ""
        self.twoFA = ""
        self.email = ""
        self.username = ""



    def map(self, data):
        if  "name" in data.keys():
            self.name = data["name"]
        self.uid = data["uid"]
        if  "lastLogin" in data.keys():
            self.lastLogin = data["lastLogin"]
        if  "lastUpdated" in data.keys():
            self.lastupdatedby = data["lastUpdated"]
        if "openId" in data.keys():
            self.open_id = data["openId"]
        self.created = data["created"]
        if "createdBy" in data.keys():
            self.created_by = data["createdBy"]
        self.surname = data["surname"]
        self.firstname = data["firstName"]
        self.disabled = data["disabled"]
        self.twoFA = data["twoFA"]
        if "email" in data.keys():
            self.email = data["email"]
        self.username = data["username"]
        if  "userRoles" in data.keys():
            data["userRoles"].sort()
            self.user_roles = json.dumps(data["userRoles"])
            self.user_roles_count = len(data["userRoles"])

