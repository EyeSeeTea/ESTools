import csv

r = csv.reader(open('users_preprod.csv'))
lines = list(r)
count = 0
row = (["username", "missing_role", "missing_group", "extra_role", "extra_group", "region", "ou"])
new_list = list()
not_match = list()
list_faltan = list()
list_sobran = list()
list_not_match = list()

clerk_groups=["NHWA Data Clerk", "NHWA Team (formerly health workforce team)", "NHWA _DATA Capture Module 1", "NHWA _DATA Capture Module 2-4", "NHWA _DATA Capture Module 5-7", "NHWA _DATA Capture Module 6", "NHWA _DATA Capture Module 8-10", "NHWA _DATA Capture NHWA Maturity assessment"]
clerk_roles=["Aggregated data entry", "Basic Access (mandatory)", "Dashboard - Aggregated data", "NHWA Data Importer App","Aggregated data use"]
manager_groups=["NHWA Data Completion", "NHWA Data Managers", "NHWA Team (formerly health workforce team)", "NHWA _DATA Capture Module 1", "NHWA _DATA Capture Module 2-4", "NHWA _DATA Capture Module 5-7", "NHWA _DATA Capture Module 6", "NHWA _DATA Capture Module 8-10", "NHWA _DATA Capture NHWA Maturity assessment"]
manager_roles=["Aggregated data approval", "Aggregated data entry", "Aggregated data use", "Aggregated data validation", "Basic Access (mandatory)", "Dashboard - Aggregated data", "NHWA Data Importer App"]
viewer_groups=["NHWA Data Viewer", "NHWA Team (formerly health workforce team)"]
viewer_roles=["Basic Access (mandatory)", "Dashboard - Aggregated data"]
admin_groups=["NHWA Data Completion", "NHWA _DATA Capture Module 8-10","NHWA Data Managers","NHWA Global Team","NHWA Team (formerly health workforce team)","NHWA _DATA Capture Module 1","NHWA _DATA Capture Module 2-4","NHWA _DATA Capture Module 5-7","NHWA _DATA Capture Module 6","NHWA _DATA Capture NHWA Maturity assessment","NHWA administrators","WIDP admins"]
admin_roles=["Aggregated data approval","Aggregated data entry","Aggregated data use","Aggregated data validation","Basic Access (mandatory)","Dashboard - Aggregated data","Dashboard - All","Data dictionary","Maintenance - Indicators Add/Update","NHWA Data Importer App","User App - Delete with managed groups","User App - Read","Users App authorities - except delete"]
reg_country="NHWA Country Team"
reg_global="NHWA Global Team"
reg_region="NHWA Regional Team"
count = 0


def groups_checker(region_groups, missing_groups, extra_groups, template_groups, item_groups):
    for template_group in template_groups:
        if template_group not in item_groups:
            if template_group != reg_country and template_group != reg_global and template_group != reg_region:
                missing_groups.append(template_group)
    for item_group in item_groups:
        if reg_global == item_group:
            if(len(region_groups)>0):
                continue
            region_groups.append(reg_global)
            continue
        if reg_country == item_group:
            if(len(region_groups)>0):
                continue
            region_groups.append(reg_country)
            continue
        if reg_region == item_group:
            if(len(region_groups)>0):
                continue
            region_groups.append(reg_region)
            continue
        if item_group not in template_groups:
            extra_groups.append(item_group)

def roles_checker(missing_roles, extra_roles, template_roles, item_roles):
    for role in template_roles:
        if role not in item_roles:
            missing_roles.append(role)
    for role in item_roles:
        if role not in template_roles:
            extra_roles.append(role)


for line in lines:
    count = count + 1
    if count == 1:
        continue
    persist = False
    match = False
    groups = line[2].split("||")
    roles = line[1].split("||")
    extra_roles = list()
    extra_groups = list()
    region_groups = list()
    missing_roles = list()
    missing_groups = list()
    if "NHWA Data Clerk" in line[2]:
        groups_checker(region_groups, missing_groups, extra_groups, clerk_groups, groups)
        roles_checker(missing_roles, extra_roles, clerk_roles, roles)
        if len(missing_groups)>0 or len(extra_groups)>0 or len(missing_roles)>0 or len(extra_roles):
            persist = True
        else:
            match = True
        type_g = "NHWA Data Clerk"
    if "NHWA Data Viewer" in line[2]:
        groups_checker(region_groups,missing_groups, extra_groups, viewer_groups, groups)
        roles_checker(missing_roles, extra_roles, viewer_roles, roles)
        if len(missing_groups)>0 or len(extra_groups)>0 or len(missing_roles)>0 or len(extra_roles):
            persist = True
        else:
            match = True
        type_g = "NHWA Data Viewer"
    if "NHWA administrators" in line[2]:
        groups_checker(region_groups,missing_groups, extra_groups, admin_groups, groups)
        roles_checker(missing_roles, extra_roles, admin_roles, roles)
        if len(missing_groups)>0 or len(extra_groups)>0 or len(missing_roles)>0 or len(extra_roles):
            persist = True
        else:
            match = True
        type_g = "NHWA administrators"
    elif "NHWA Data Managers" in line[2]:
        groups_checker(region_groups,missing_groups, extra_groups, manager_groups, groups)
        roles_checker(missing_roles, extra_roles, manager_roles, roles)
        if len(missing_groups)>0 or len(extra_groups)>0 or len(missing_roles)>0 or len(extra_roles):
            persist = True
        else:
            match = True
        type_g = "NHWA Data Managers"
    country = "not match"
    if len(region_groups)>0:
        country = region_groups
    if persist:
        new_list.append([line[0], type_g, extra_roles, missing_roles, extra_groups, missing_groups, line[3], line[4], country, line[1], line[2]])
    else:
        if match:
            new_list.append([line[0], type_g, extra_roles, missing_roles, extra_groups, missing_groups, line[3], line[4], country, line[1], line[2]])
        else:
            new_list.append([line[0], "not_match", "not match", "not match", "not match", "not match", line[3], line[4], country, line[1], line[2]])

writer = csv.writer(open('hwf_users_post_harmonization_preprod.csv', 'w'))
writer.writerows([["username", "type", "extra_roles", "missing_roles", "extra_groups", "missing_groups", "OUCapture", "OUOutput", "region", "all roles", "all groups"]])
writer.writerows(new_list)