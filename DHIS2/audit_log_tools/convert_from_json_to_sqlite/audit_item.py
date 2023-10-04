import json
import json

from user_audit import UserAudit
from usergroup_audit import UserGroupAudit


class AuditItem:
    def __init__(self):
        self.audit_type = ""
        self.createdat = ""
        self.createdby = ""
        self.klass = ""
        self.uid = ""
        self.name = ""
        self.listofattributes = ""
        self.user_group = UserGroupAudit()
        self.user = UserAudit()

    # Método adicional (opcional)
    def map(self, json_data):
        self.audit_type = json_data["auditType"]
        self.createdat = json_data["createdAt"]
        self.createdby = json_data["createdBy"]
        self.klass = json_data["klass"]
        if "uid" in json_data.keys():
            self.uid = json_data["uid"]
        else:
            print("nouid")
        self.name = ""
        self.listofattributes = json.dumps(json_data["attributes"])
        if "org.hisp.dhis.user.UserGroup" == self.klass:
            data = json_data["data"]
            self.user_group.map(data)
        elif "org.hisp.dhis.user.User" == self.klass:
            data = json_data["data"]
            self.user.map(data)

