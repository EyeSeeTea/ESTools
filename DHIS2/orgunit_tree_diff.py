import psycopg2
import csv

def con(database, user, password, host):
    conn = psycopg2.connect(
       database=database, user=user, password=password, host=host, port= '5432'
    )
    return conn

def get_rows(host):
    con_prod = con("dhis2", "dhis", "dhis", host)
    cur_p = con_prod.cursor()
    cur_p.execute("SELECT uid, path, name, shortname, code FROM organisationunit")

    rows = cur_p.fetchall()
    print("The number of parts: ", cur_p.rowcount)
    con_prod.close()
    return rows


def iterate_queries(prod_rows, dev_rows, filename):
    with open(filename, mode='w') as employee_file:
        employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        employee_writer.writerow(['uid', 'path', 'name', 'shortName', 'code','uid', 'path', 'name', 'shortName', 'code'])
        for row in prod_rows:
            for dev_row in dev_rows:
                if (row[0] == dev_row[0]):
                    if (row == dev_row):
                        d = row+ dev_row
                        employee_writer.writerow(d)
                        continue
                    else:
                        d = row
                        employee_writer.writerow(d)
                        continue


prod_rows = get_rows("172.27.0.2")
dev_rows = get_rows("172.24.0.2")
iterate_queries(prod_rows, dev_rows, "prod-dev.csv")
print("dev to prod")
iterate_queries(dev_rows,prod_rows, "dev-prod.csv")
