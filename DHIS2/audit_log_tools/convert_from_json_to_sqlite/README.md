unifiedtodb.py is a python script to convert json file into dbaudit database. 
Note: if you execute it multiple times you will add repeated audits in the database, you need remove all data first to have a clean database.
convert .json into sqldb to easiest query and understand the audit data. Only user and usergroups convert all the interesting types at this point.
example of query:
select a.createdby, a.createdat, ug.ug_members, ug.ug_members_count, ug_sharing_ug_count, ug_createdby, ug.ug_uid, ug_lastupdated, ug_lastupdatedby  from audit a join usergroup ug on a.auditid = ug.ug_auditid where ug_name like '%NHWA%' order by createdat DESC;