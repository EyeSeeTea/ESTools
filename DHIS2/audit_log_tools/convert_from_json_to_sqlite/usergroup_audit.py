import json


class UserGroupAudit:
    def __init__(self):
        self.uid = ""
        self.lastupdated = ""
        self.lastupdatedby = ""
        self.createdby = ""
        self.created = ""
        self.members = ""
        self.members_count = ""
        self.name = ""
        self.sharing = ""
        self.sharing_ug_count = ""
        self.sharing_u_count = ""
        self.publicaccess = ""


    def map(self, data):
        if "name" in data.keys():
            self.name = data["name"]
        self.uid = data["uid"]
        self.lastupdated = data["lastUpdated"]
        if "lastUpdatedBy" in data.keys():
            self.lastupdatedby = data["lastUpdatedBy"]
        self.createdby = data["createdBy"]
        self.created = data["created"]
        if "members" in data.keys():
            data["members"].sort()
            self.members = json.dumps(data["members"])
            self.members_count = len(data["members"])
        if "sharing" in data.keys():
            self.sharing = json.dumps(data["sharing"])
            self.sharing_u_count = len(data["sharing"]["users"])
            self.sharing_ug_count = len(data["sharing"]["userGroups"])
            self.publicaccess = data["sharing"]["public"]
