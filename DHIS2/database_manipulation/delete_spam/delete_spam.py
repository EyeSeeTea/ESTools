#!/usr/bin/env python3

"""
Delete "spam" messages that arrived because of a bug in a report that are older than one week.

Usage:

Example of
python3 ./delete_spam.py --dsn "host=localhost port=$docker_port dbname=dhis2 user=dhis"

"""

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import psycopg2


def main():
    args = get_args()

    try:
        with psycopg2.connect(args.dsn) as conn:
            with conn.cursor() as cur:
                delete_spam(cur, args.uids.split(','), args.subject)

    except (AssertionError, ValueError) as e:
        sys.exit(e)


def get_args():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)

    add = parser.add_argument  # shortcut
    add('--uids',
        default='kD52FGwJgDF,YdBcEIZpRHo,zu8v89yqrBV,H4atNsEuKxP,fa7DnTkWEOL,hfaMYUsDm8u',
        help='comma separated list of uids of users that received spam to delete')
    # by default, the ones they asked us to remove of spam messages
    add('--subject', default=r'WMR Form monitoring%',
        help='Pattern in the subject of the spam messages')
    add('--dsn', default='host=localhost dbname=dhishq user=dhishq_usr',
        help='data source name (string that describes the connection)')

    return parser.parse_args()


def delete_spam(cur, uids_spammed, subject):
    cur.execute(f"SELECT messageid FROM message "
                f"  WHERE messagetext LIKE '{subject}'"
                f"    AND created < NOW() - INTERVAL '7 days';")
    spam_mids = cur.fetchall()

    for mid in spam_mids:
        mid = mid[0]

        cur.execute(f'SELECT messageconversationid FROM messageconversation_messages '
                    f'  WHERE messageid = {mid}')
        mcid = cur.fetchall()
        assert len(mcid) == 1, 'len(mcid) = %d' % len(mcid)
        mcid = mcid[0][0]

        print(f'messageid = {mid}  messageconversationid = {mcid}')

        cur.execute(f'SELECT usermessageid FROM messageconversation_usermessages '
                    f'  WHERE messageconversationid = {mcid}')
        umids = cur.fetchall()

        all_recipients_spam = True
        for umid in umids:
            umid = umid[0]
            cur.execute(f'SELECT uid FROM userinfo '
                        f'  WHERE userinfoid = ('
                        f'    SELECT userid FROM usermessage '
                        f'      WHERE usermessageid = {umid})')
            uid = cur.fetchall()
            assert len(uid) == 1
            uid = uid[0][0]

            if uid in uids_spammed:
                cur.execute(f'DELETE FROM messageconversation_usermessages '
                            f'  WHERE usermessageid = {umid}')
                cur.execute(f'DELETE FROM usermessage '
                            f'  WHERE usermessageid={umid}')
            else:
                print('This unknown uid got spam:', uid)
                all_recipients_spam = False

        if all_recipients_spam:
            cur.execute(f'DELETE FROM messageconversation_messages '
                        f'  WHERE messageconversationid = {mcid}')
            cur.execute(f'DELETE FROM messageconversation '
                        f'  WHERE messageconversationid = {mcid}')
            cur.execute(f'DELETE FROM message '
                        f'  WHERE messageid = {mid}')


if __name__ == '__main__':
    main()
