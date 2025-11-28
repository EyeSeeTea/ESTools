SQL_FIND_ORPHANS_DOCUMENTS = """
    SELECT fileresourceid, uid, storagekey, name, created
    FROM fileresource fr
    WHERE NOT EXISTS (
        SELECT 1 FROM document d WHERE d.fileresource = fr.fileresourceid
    )
    AND fr.uid NOT IN (
        SELECT url FROM document
    )
    AND fr.domain = 'DOCUMENT' and  fr.storagekey like '%document%';
"""

SQL_FIND_DATA_VALUES_FILE_RESOURCES = """
    SELECT fileresourceid, uid, storagekey, name, created
    FROM fileresource fr where fr.domain = 'DATA_VALUE' and  fr.storagekey like '%dataValue%';
"""

SQL_INSERT_AUDIT = """
    INSERT INTO fileresourcesaudit SELECT * FROM fileresource WHERE fileresourceid = %(fid)s;
"""

SQL_DELETE_ORIGINAL = """
    DELETE FROM fileresource WHERE fileresourceid = %(fid)s;
"""

SQL_CREATE_TABLE_IF_NOT_EXIST = """
    CREATE TABLE IF NOT EXISTS fileresourcesaudit AS TABLE fileresource WITH NO DATA;
"""

SQL_EVENT_FILE_UIDS = """
        SELECT eventdatavalues
        FROM event
        WHERE programstageid 
        IN (SELECT programstageid FROM programstagedataelement WHERE dataelementid  
        IN (SELECT dataelementid FROM dataelement WHERE valuetype='FILE_RESOURCE' or valuetype='IMAGE')) and deleted='f';
"""

SQL_DATA_VALUE_UIDS = """
        SELECT dv.value
        FROM datavalue dv
        WHERE dv.value IN (SELECT uid FROM fileresource WHERE domain='DATA_VALUE')
"""

SQL_TRACKER_ATTRIBUTE_UIDS = """
select value from trackedentityattributevalue where value IN (SELECT uid FROM fileresource WHERE domain='DATA_VALUE');
"""
