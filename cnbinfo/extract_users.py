#!/usr/bin/env python3

"""
Get a list of the machines and user names and ids.
"""

import sys
import os

users_not_valid = {
    'root', 'admin', 'sync', 'ftp',
    'backup', 'list', 'bin', 'irc', 'daemon', 'games', 'gnats', 'zabbix',
    'news', 'nobody', 'postgres', 'Debian-exim', 'halt', 'shutdown',
    'proxy', 'sys', 'uucp', 'www-data', 'slurm', 'supervisor', 'buildbot',
    'libuuid', 'lp', 'mail', 'man', 'speech-dispatcher',
    'xgbpred', 'bionotes', 'pdb_pssm', 'dimero',
    'curso01', 'curso02', 'curso03', 'curso04', 'curso05', 'curso06', 'curso07',
    'curso08', 'curso09', 'curso10', 'curso11', 'curso12', 'curso13',
    'demo00', 'demo01', 'demo02', 'demo03', 'demo04', 'demo05',
    'demo06', 'demo07', 'demo08', 'demo09', 'demo10',
    'trial01', 'trial02', 'trial03', 'trial04', 'trial05', 'trial06', 'trial07',
    'trial08', 'trial09', 'trial10', 'trial11', 'trial12', 'trial13', 'trial14',
    'trial17'}



def main():
    users_info = {machine: users for machine, users in get_users()}
    for machine in sorted(users_info.keys()):
        for user in users_info[machine]:
            print('%s,%s' % (nice_name(machine), ','.join(user)))


def nice_name(name):
    "Return name of the machine as we normally call them"
    return name[4:] if name.startswith('cnb-') else name
    # The cnb-* is related to my aliases in .ssh/config


def get_users():
    "Yield pairs of (machine, list_of_users), as read from users.txt"
    if not os.path.exists('users.txt'):
        sys.exit("""users.txt missing. You can generate it by running:
  ./multirun.py --literal 'cat /etc/passwd' > users.txt""")

    users_current = []
    machine_current = None
    for line in open('users.txt'):
        if new_machine(line):
            if machine_current:
                yield machine_current, users_current
            machine_current = line.split()[0]
            users_current = []
        else:
            name, _, uid, _, _, home, shell = line.strip().split(':')
            if is_good_user(name, shell):
                users_current.append( (name, uid) )
    yield machine_current, users_current  # the last one


def is_good_user(name, shell):
    "Return True iff the user is one we want"
    return (not any(shell.endswith(x) for x in ['/nologin', '/false']) and
            name not in users_not_valid)


def new_machine(line):
    "Return True iff the line contains the output from a new machine"
    return len(line.split()) > 1 and line.find(' ') < line.find(':')



if __name__ == '__main__':
    main()
