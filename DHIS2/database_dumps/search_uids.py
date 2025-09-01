#!/usr/bin/env python3

"""
Search uids in a dump or sql file.
"""

import sys
from subprocess import Popen, PIPE


def main():
    if len(sys.argv) < 3:
        sys.exit(f'usage: {sys.argv[0]} FILE UID [UID ...]')

    fname = sys.argv[1]
    uids = sys.argv[2:]

    cmd = (['pg_restore', fname] if fname.endswith('.dump') else
           ['cat', fname])

    print(f'Tables and columns in {fname} where any of the uids appear:')

    sqldata = Popen(cmd, stdout=PIPE)
    print_uid_appearances(sqldata.stdout, uids)


def print_uid_appearances(sqldata, uids):
    "Print tables and columns where any of the uids appear in the given data"
    table = None
    cols = None
    already_reported_table = False

    for bline in sqldata:
        line = bline.decode('utf8')

        if line.startswith('COPY public.'):  # start of new table data
            already_reported_table = False
            table_start = len('COPY public.')
            table_end = line.find(' ', table_start)
            cols_start = table_end + len(' (')
            cols_end = line.find(')', cols_start)
            table = line[table_start:table_end]
            cols = line[cols_start:cols_end].split(', ')

        if any(uid in line for uid in uids) and table is not None:
            if not already_reported_table:
                print(f'\n-- {table} --')
                already_reported_table = True

            for i, field in enumerate(line.rstrip().split('\t')):
                if any(uid in field for uid in uids):
                    print(f'{cols[i]} -> {field}')



if __name__ == '__main__':
    main()
