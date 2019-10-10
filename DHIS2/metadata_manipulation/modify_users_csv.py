import csv

import numpy as np

r = csv.reader(open('hwf_users_in_prod.csv'))
lines = list(r)
count = 0
new_list = list()
all_users = list()
number_of_files=len(lines)/200
if type(number_of_files) is float:
    number_of_files = int(number_of_files)+1


new_list = np.empty(number_of_files, dtype=np.object)
for i in range(new_list.shape[0]):
    new_list[i] = list()
    new_list[i].append(lines[0])
other = list()
other.append(lines[0])
count = 0
for line in lines:
    count = count +1
    persist = False
    if "||NHWA Data Clerk" in line[3] or "NHWA Data Clerk" in line[3]:
        if not ("Aggregated data entry" in line[1] and "Aggregated data validation" not in line[1]):
            persist = True
            line[3] = line[3].replace("||NHWA Data Clerk", "")
            line[3] = line[3].replace("NHWA Data Clerk", "")
            print("removing data cleck from " + line[0])
    if "Aggregated data entry" in line[1] and "Aggregated data validation" not in line[1]:
        persist = True
        line[3] = line[3] + "||NHWA Data Clerk"
    if "Aggregated data approval" in line[1] or "Aggregated data validation" in line[1]:
        persist = True
        line[3] = line[3] + "||NHWA Data Managers"
    if "Aggregated data entry" not in line[1] and "Dashboard - Aggregated data" in line[1]:
        persist = True
        line[3] = line[3] + "||NHWA Data Viewer"
    if "NHWA Data Managers" in line[3] and "Maintenance - " in line[1]:
        persist = True
        line[3] = line[3] + "||NHWA administrators"
    if persist:
        new_list[int(count/200)].append(line)
        all_users.append(line)
    else:
        print("not match: " + line[0])

print("data Clerk----------------------")
for line in all_users:
    count = count + 1
    if count > 1:
        if "NHWA Data Clerk" in line[3]:
            print(line[0])
print("data Managers----------------------")
for line in all_users:
    count = count + 1
    if count > 1:
        if "NHWA Data Managers" in line[3]:
            print(line[0])
print("data Viewer----------------------")
for line in all_users:
    count = count + 1
    if count > 1:
        if "NHWA Data Viewer" in line[3]:
            print(line[0])
print("data administrators----------------------")
for line in all_users:
    count = count + 1
    if count > 1:
        if "NHWA administrators" in line[3]:
            print(line[0])

for i in range(new_list.shape[0]):
    writer = csv.writer(open('hwf_users_in_prod_fixed_'+str(i)+'.csv', 'w'))
    writer.writerows(new_list[i])