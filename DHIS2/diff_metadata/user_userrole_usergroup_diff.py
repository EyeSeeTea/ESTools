import json
import sys


def compare_user_roles_and_groups(json1, json2):
    result = {"users": []}

    users1 = {user['id']: user for user in json1['users']}
    users2 = {user['id']: user for user in json2['users']}

    for user_id, user1 in users1.items():
        if user_id in users2:
            user2 = users2[user_id]

            roles1 = {role['name']: role['id'] for role in user1['userRoles']}
            roles2 = {role['name']: role['id'] for role in user2['userRoles']}

            missing_roles_in_1 = [(role_name, roles2[role_name])
                                  for role_name in roles2 if role_name not in roles1]
            missing_roles_in_2 = [(role_name, roles1[role_name])
                                  for role_name in roles1 if role_name not in roles2]

            groups1 = {group['id']: group['name']
                       for group in user1['userGroups']}
            groups2 = {group['id']: group['name']
                       for group in user2['userGroups']}

            missing_groups_in_1 = [(group_id, groups2[group_id])
                                   for group_id in groups2 if group_id not in groups1]
            missing_groups_in_2 = [(group_id, groups1[group_id])
                                   for group_id in groups1 if group_id not in groups2]

            if missing_roles_in_1 or missing_roles_in_2 or missing_groups_in_1 or missing_groups_in_2:
                result['users'].append({
                    "id": user1["id"],
                    "username": user1["username"],
                    "missingRolesIn1": missing_roles_in_1,
                    "missingRolesIn2": missing_roles_in_2,
                    "missingGroupsIn1": missing_groups_in_1,
                    "missingGroupsIn2": missing_groups_in_2
                })

    return result


def print_human_readable(result, file1, file2):
    for user in result['users']:
        print(f"User: {user['username']} (ID: {user['id']})")

        if user['missingRolesIn1']:
            print(f"  Missing roles in {file1}:")
            for role_name, role_id in user['missingRolesIn1']:
                print(f"    - {role_id}: {role_name}")

        if user['missingRolesIn2']:
            print(f"  Missing roles in {file2}:")
            for role_name, role_id in user['missingRolesIn2']:
                print(f"    - {role_id}: {role_name}")

        if user['missingGroupsIn1']:
            print(f"  Missing groups in {file1}:")
            for group_id, group_name in user['missingGroupsIn1']:
                print(f"    - {group_id}: {group_name}")

        if user['missingGroupsIn2']:
            print(f"  Missing groups in {file2}:")
            for group_id, group_name in user['missingGroupsIn2']:
                print(f"    - {group_id}: {group_name}")

        print("")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: script.py file1.json file2.json")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    try:
        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            json1 = json.load(f1)
            json2 = json.load(f2)
    except Exception as e:
        print(f"Error reading files: {e}")
        sys.exit(1)

    comparison_result = compare_user_roles_and_groups(json1, json2)

    print_human_readable(comparison_result, file1, file2)
