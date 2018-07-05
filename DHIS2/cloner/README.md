# Cloner utils

Run full clone process:

```
$ python dhis2_clone.py --config=dhis2_clone.json
```

## Standalone processing

### Enable users

Example: Enable all users within user groups _Malaria program_ and _Facility tracker_:

```
$ python process.py --url=http://localhost:8080 --username=system --password=System123 enable-users "Malaria program" "Facility tracker"
```

### Add user roles

Example: Use (add-user-roles.example.json)[add-user-roles.example.json] to add user roles from `userTemplate` and `extraUserRoles` to every user in `userGroups`:

```
$ python process.py --url=http://localhost:8080 --username=system --password=System123 add-user-roles add-user-roles.example.json
```
