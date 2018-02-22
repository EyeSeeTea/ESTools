#!/usr/bin/env python3

"""
Simple monitor for the status of the computers tracked at CNB.
"""

import os
import time
import logging
import subprocess as sp
from concurrent.futures import ThreadPoolExecutor as Pool
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import daemonize

PATH = os.path.dirname(os.path.realpath(__file__))
LOGFILE = os.path.join(PATH, 'monitor.log')
STATUSFILE = os.path.join(PATH, 'last_status.txt')

# The following variables would need to be properly filled to run it.
EMAIL_USER = ''
EMAIL_PASSWD = ''

webs = []
processing = []
storage = []
backups = []

machines = set(webs + processing + storage + backups)

dead = []
disappeared = []
# End of variables that need to be filled.


status_meaning = {0: 'OK', 1: 'Dead', 2: 'Ping error'}


def main():
    args = parse_arguments()
    if not args.no_daemon:
        daemonize.daemonize()
    start_logging(args.logfile, args.loglevel)
    notify = choose_notify_function(args.notify, args.recipients)
    check_periodically(args.interval, notify)


def parse_arguments():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('--no-daemon', action='store_true', help='keep attached to the console')
    add('--logfile', default=LOGFILE, help='path of the file with the logs')
    add('--loglevel', default=logging.DEBUG, help='logger verbosity level')
    add('--notify', choices=['email', 'print'], default='email',
        help='method used for notification')
    add('--recipients', nargs='*', metavar='RECIPIENT',
        default=['jordi@eyeseetea.com'], help='email recipients')
    add('--interval', type=int, default=60, help='time (in s) between checks')
    return parser.parse_args()


def start_logging(logfile, loglevel):
    logging.basicConfig(filename=logfile, level=loglevel,
                        format='%(asctime)s [%(levelname)s] %(message)s')
    logging.info('Starting.')
    logging.debug('Current directory is %s' % os.getcwd())


def choose_notify_function(method, recipients):
    "Return a function used to notify"
    if method == 'email':
        return lambda text: send_email(recipients=recipients,
                                       subject='cnb machines status', body=text)
    elif method == 'print':
        return print  # the print function


def check_periodically(interval, notify):
    "Check status of the machines every interval seconds, notify if necessary"
    last_status = get_initial_status()
    while True:
        logging.debug('Checking machines status...')
        status = associate(get_status, machines)
        if status != last_status:
            logging.warn('Changes found. Notifying.')
            notify(describe(status, last_status))
        else:
            logging.info('No changes.')
        last_status = status
        save_status(status)
        time.sleep(interval)


def get_initial_status():
    "Return the status inferred from existing machines, dead and disappeared"
    status = lambda m: (2 if m in disappeared else 1 if m in dead else 0)
    return {m: status(m) for m in machines}


def describe(status, last_status):
    "Return a text explaining the status of the machines"
    last_fails = {m for m in machines if last_status[m] != 0}
    fails = {m for m in machines if status[m] != 0}
    bad_changes = fails - last_fails
    good_changes = last_fails - fails
    text = 'Status of the machines at CNB\n\n'
    if bad_changes:
        text += '\n\nWere working but stopped:\n  ' + '\n  '.join(bad_changes)
    if good_changes:
        text += '\n\nWere not working but do:\n  ' + '\n  '.join(good_changes)
    text += '\n\nAll machines:\n'
    for m in machines:
        text += '  %-12s %s\n' % (status_meaning[status[m]], m)
    return text


def associate(f, a, max_workers=10):
    "Return {x: f(x) for x in a} computed in parallel"
    a = list(a)  # in case it was a set, to respect the order
    with Pool(max_workers) as pool:
        return dict(zip(a, pool.map(f, a)))


def get_status(machine, deadline=3):
    "Return status from making a single ping to the given machine"
    return sp.call(['ping', '-c', '1', '-w', '%d' % deadline, machine],
                   stdout=sp.DEVNULL, stderr=sp.DEVNULL)


def send_email(recipients, subject, body):
    "Send email to recipients with the given subject and body text"
    sp.call(['sendEmail', '-s', 'smtp.gmail.com:587', '-o', 'tls=yes',
             '-xu', EMAIL_USER, '-xp', EMAIL_PASSWD,
             '-f', EMAIL_USER, '-u', subject, '-m', body] +
            ['-t'] + recipients, stdout=sp.DEVNULL, stderr=sp.DEVNULL)


def save_status(status):
    "Save the given status to disk"
    with open(STATUSFILE, 'wt') as f:
        f.write('\n'.join('%d %s' % (s, m) for m, s in status.items()))


def load_last_status():
    "Return status as loaded from disk"
    status = {}
    for line in open(STATUSFILE):
        s, m = line.strip().split(' ', 1)
        status[m] = int(s)
    return status



if __name__ == '__main__':
    main()
