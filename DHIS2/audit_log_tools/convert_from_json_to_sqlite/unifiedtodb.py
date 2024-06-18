import sqlite3
import ijson

from audit_item import AuditItem

# Conectar a la base de datos SQLite, si no existe, se creará automáticamente
conn = sqlite3.connect('dbaudit.db')

# Crear un cursor para ejecutar consultas SQL
cursor = conn.cursor()

# Definir los datos que deseas insertar en la tabla

file = "filtered_logs__ALL_ALL_ALL.json"
with open(file, "r", encoding="utf-8") as infile:
    #data = ijson.load(infile)
    audit=[]
    objects = ijson.items(infile, 'audit.item')
    for item in objects:
        if item["auditScope"] == "METADATA":
            audit_item = AuditItem()
            audit_item.map(item)
            audit.append(audit_item)
            print("append")

    for audit_item in audit:
        cursor.execute('''INSERT INTO audit (
        auditid, auditype, createdat, createdby, klass, uid, name, listofattributes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (None,
                                                                                audit_item.audit_type,
                                                                                audit_item.createdat,
                                                                                audit_item.createdby, audit_item.klass,
                                                                                audit_item.uid, audit_item.name,
                                                                                audit_item.listofattributes))

        # Commit (guardar) los cambios
        conn.commit()

        last_id = cursor.lastrowid
        if audit_item.klass == "org.hisp.dhis.user.UserGroup":
            cursor.execute('''INSERT INTO usergroup (usergroupid,
                    ug_uid, ug_lastupdated, ug_lastupdatedby, ug_createdby, 
                    ug_members, 
                    ug_members_count, ug_name, ug_sharing, ug_sharing_ug_count, 
                    ug_sharing_u_count, ug_publicaccess, ug_auditid
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (None,
                                                                          audit_item.user_group.uid,
                                                                          audit_item.user_group.lastupdated,
                                                                          audit_item.user_group.lastupdatedby,
                                                                          audit_item.user_group.createdby,
                                                                          audit_item.user_group.members,
                                                                          audit_item.user_group.members_count,
                                                                          audit_item.user_group.name,
                                                                          audit_item.user_group.sharing,
                                                                          audit_item.user_group.sharing_ug_count,
                                                                          audit_item.user_group.sharing_u_count,
                                                                          audit_item.user_group.publicaccess,
                                                                          last_id))

            # Commit (guardar) los cambios
            conn.commit()

        if audit_item.klass == "org.hisp.dhis.user.User":
            cursor.execute('''INSERT INTO user (userid,
                    u_lastlogin, u_lastupdated, u_openid, u_created, 
                    u_user_roles, 
                    u_user_roles_count, u_createdby, u_surname, u_firstname, 
                    u_disabled, u_twofa, u_email, u_username, u_auditid
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)''', (None,
                                                                          audit_item.user.lastLogin,
                                                                          audit_item.user.lastUpdated,
                                                                          audit_item.user.open_id,
                                                                          audit_item.user.created,
                                                                          audit_item.user.user_roles,
                                                                          audit_item.user.user_roles_count,
                                                                          audit_item.user.created_by,
                                                                          audit_item.user.surname,
                                                                          audit_item.user.firstname,
                                                                          audit_item.user.disabled,
                                                                          audit_item.user.twoFA,
                                                                          audit_item.user.email,
                                                                          audit_item.user.username,
                                                                          last_id))

            # Commit (guardar) los cambios
            conn.commit()

# Cerrar la conexión
conn.close()
