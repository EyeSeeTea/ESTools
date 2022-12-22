#!/usr/bin/env python3

"""
Delete audits for certain dataelements.
"""

# Reference ticket: https://app.clickup.com/t/3ajztx7

# Delete the audit trail for data elements with the following Prefixes
# and Suffixes:
#
# Prefix:
#   MAL - FINAL
#   MAL - Calc -
#   MAL - PARAM
#   (DEL)
#   (OLD)
#
# Suffix:
#   - Annex
#   - CPROFIL
#   - App

# The tables in dhis2 that have "audit" in their name are:
#   audit
#   dataapprovalaudit
#   datavalueaudit
#   metadataaudit
#   programtempownershipaudit
#   trackedentityattributevalueaudit
#   trackedentitydatavalueaudit
#   trackedentityinstanceaudit
#
# where "audit" seems to be the big one (at least in dev).
#
# To get the size of the tables:
#   SELECT table_name, pg_relation_size(quote_ident(table_name))
#   FROM information_schema.tables
#   WHERE table_schema = 'public'
#   ORDER BY 2;

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import psycopg2


def main():
    args = get_args()

    try:
        with psycopg2.connect(args.dsn) as conn:
            with conn.cursor() as cur:
                uids = get_uids(cur, args.prefixes, args.suffixes)
                assert uids, 'No dataelements match the prefixes and suffixes.'
                rm_audits(cur, uids)

    except (AssertionError, psycopg2.OperationalError) as e:
        sys.exit(e)


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)

    add = parser.add_argument  # shortcut
    add('-p', '--prefixes', nargs='*', default=[],
        help='prefixes of dataelements to select')
    add('-s', '--suffixes', nargs='*', default=[],
        help='suffixes of dataelements to select')
    add('--dsn', default='host=localhost dbname=dhishq user=dhishq_usr',
        help='data source name (string that describes the connection)')

    return parser.parse_args()


def get_uids(cur, prefixes, suffixes):
    "Return list of uids of dataelements identified by the given pre/suffixes"
    assert prefixes or suffixes, 'No prefixes nor suffixes specified.'

    print('Selecting dataelments that match the given prefixes and suffixes...')

    conditions = ([f"name LIKE '{p}%%'" for p in prefixes] +
                  [f"name LIKE '%%{s}'" for s in suffixes])

    cur.execute('SELECT uid FROM dataelement WHERE ' + ' OR '.join(conditions))
    return [x[0] for x in cur.fetchall()]


def rm_audits(cur, uids):
    "Remove audits related to the given uids"
    print('Deleting audits...')
    cur.execute('DELETE FROM audit WHERE uid IN (%s)' %
                (','.join(f"'{uid}'" for uid in uids)))
    print(cur.statusmessage)



if __name__ == '__main__':
    main()
