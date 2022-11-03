#!/usr/bin/env python3

"""
Print usernames and their openids, as they exist in a database dump.
"""

import sys
import os
from subprocess import Popen, PIPE


def main():
    backups = sys.argv[1:]

    if not backups:
        sys.exit(f'usage: {sys.argv[0]} BACKUP1 [BACKUP2 ...]')

    for backup in backups:
        print(f'Showing users and openids defined in {backup} ...')
        sqldata = Popen(['pg_restore', '-f', '-', backup], stdout=PIPE)
        for user,openid in get_openids(sqldata.stdout):
            print('%22s  %s' % (user, openid))


def get_openids(sqldata):
    "Yield pairs of (username, openid) from the given data"
    users_section = False
    for line in sqldata:
        if not users_section:
            if line.startswith(b'COPY public.users '):
                users_section = True
        else:
            if len(line) < 5:
                return

            parts = line.decode('utf8').split('\t')
            yield parts[6], parts[9].replace(r'\N', '<none>')



if __name__ == '__main__':
    main()
