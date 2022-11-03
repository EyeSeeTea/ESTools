#!/usr/bin/env python3

"""
Update datavalues based on expression.

The update is for all countries for the given year, and happens only
if the value does not already coincide.
"""

# TODO: Make version using api calls.
# See datavalueSet endpoint for that.

import sys
import re
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
from math import pi, inf, sqrt, sin, cos, tan, atan2

import psycopg2


context_math = {  # operations that can be used in the expression
    'sum': sum, 'abs': abs, 'float': float, 'int': int, 'pi': pi, 'inf': inf,
    'sqrt': sqrt, 'sin': sin, 'cos': cos, 'tan': tan, 'atan2': atan2}



def main():
    args = get_args()

    try:
        with psycopg2.connect(args.dsn) as conn:
            with conn.cursor() as cur:
                update_all(cur, args.dataelement, args.expression, args.year)
    except (AssertionError, ValueError) as e:
        sys.exit(e)


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)

    add = parser.add_argument  # shortcut
    add('--dataelement', default='h6VJJu0W8U7',
        help='uid of the dataelement to update')
    add('--expression', default='Yxkvq7nmosQ + Ta8ifRxwOmP + jj5ZtVGdcwd',
        help='expression to use for the update')
    add('--year', type=int, default=2021, help='year of the data to update')
    add('--dsn', default='host=localhost dbname=dhishq user=dhishq_usr',
        help='data source name (string that describes the connection)')

    return parser.parse_args()


def update_all(cur, dataelement, expression, year):
    "Update dataelement according to expression, year, and in all countries"
    uid_pattern = r'\b[a-zA-Z]\w{10}\b'

    assert re.fullmatch(uid_pattern, dataelement), \
        f'invalid datalement uid: {dataelement}'
    y = dataelement  # just for consistent notation
    xs = re.findall(uid_pattern, expression)

    y_id = get_dataelement_id(cur, y)
    x_ids = [get_dataelement_id(cur, x) for x in xs]

    period_id = get_period_id(cur, year)

    code = compile(expression, '<string>', 'eval')

    print('%21s == %s\n' % (y, expression))

    for ou_id, ou_name in get_orgunits(cur):
        y_v = get_value(cur, y_id, ou_id, period_id)
        x_vs = [get_value(cur, x_id, ou_id, period_id) for x_id in x_ids]

        if any(x_v is None for x_v in x_vs):
            if y_v is not None:
                print(f'Oops, inconsistent values in {ou_name}:', y_v, *x_vs)
            continue  # skip this country in any case

        print('%-15s %5d == %-20s ' % (
            ou_name, y_v, 'f(' + ', '.join(str(v) for v in x_vs) + ')'), end='')

        values = {x: v for x,v in zip(xs, x_vs)}
        context = dict(context_math, **values)
        result = safer_eval(code, context)

        if y_v == result:
            print('true')
        else:
            print(f'false -- updating {y_v} -> {result} ...')
            update_value(cur, y_id, ou_id, period_id, result)


def get_dataelement_id(cur, uid):
    cur.execute(f"SELECT dataelementid FROM dataelement WHERE uid='{uid}'")
    return cur.fetchone()[0]

def get_period_id(cur, year):
    cur.execute(f"SELECT periodid FROM period "
                f"WHERE startdate='{year}-01-01' AND enddate='{year}-12-31'")
    return cur.fetchone()[0]

def get_orgunits(cur):
    cur.execute('SELECT organisationunitid,shortname FROM organisationunit '
                'WHERE hierarchylevel=3')
    return cur.fetchall()

def get_value(cur, dataelement_id, ou_id, period_id):
    cur.execute(f'SELECT value FROM datavalue '
                f'WHERE dataelementid={dataelement_id} '
                f'  AND sourceid={ou_id} '
                f'  AND periodid={period_id}')
    result = cur.fetchone()
    return int(result[0]) if result and result[0] is not None else None

def update_value(cur, y_id, ou_id, period_id, result):
    cur.execute(f'UPDATE datavalue SET value={result} '
                f'WHERE dataelementid={y_id} '
                f'  AND sourceid={ou_id} '
                f'  AND periodid={period_id}')


def safer_eval(code, context):
    "Return a safer version of eval(code, context)"
    for name in code.co_names:
        if name not in context:
            raise ValueError('invalid use of %r during evaluation' % name)
    return eval(code, {'__builtins__': {}}, context)



if __name__ == '__main__':
    main()
