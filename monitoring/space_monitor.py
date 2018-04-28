#!/usr/bin/env python3

"""
Alert whenever more than 80% of the quota (or available space) is used.
"""

import sys
import os
import time
import logging
import subprocess as sp
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import daemonize

PATH = os.path.dirname(os.path.realpath(__file__))
LOGFILE = os.path.join(PATH, 'space_monitor.log')
STATUSFILE = os.path.join(PATH, 'last_space_status.txt')

# The following variables would need to be properly filled to run it.
EMAIL_USER = ''
EMAIL_PASSWD = ''

ZFS_DATASET = ''

mails_datasets = {}
datasets = mails_datasets.keys()

mails_users = {}
users = mails_users.keys()

mails_all = {}
mails_all.update(mails_datasets)
mails_all.update(mails_users)
spaces = mails_all.keys()

last_notification_time = {space: 0 for space in mails_all.keys()}
# End of variables that need to be filled.



def main():
    args = parse_arguments()
    if not args.no_daemon:
        daemonize.daemonize()
    start_logging(args.logfile, args.loglevel)
    notify = choose_notify_function(args.notify)
    check_periodically(args.interval, args.throttle_days, args.warning_level,
                       notify)


def parse_arguments():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('--no-daemon', action='store_true', help='keep attached to the console')
    add('--logfile', default=LOGFILE, help='path of the file with the logs')
    add('--loglevel', default=logging.DEBUG, help='logger verbosity level')
    add('--throttle-days', default=7, help='number of days between warning reminders')
    add('--notify', choices=['email', 'print'], default='email',
        help='method used for notification')
    add('--interval', type=int, default=60, help='time (in s) between checks')
    add('--warning-level', type=float, default=0.80,
        help='fraction of space used above which we send a warning')
    return parser.parse_args()


def start_logging(logfile, loglevel):
    logging.basicConfig(filename=logfile, level=loglevel,
                        format='%(asctime)s [%(levelname)s] %(message)s')
    logging.info('Starting.')
    logging.debug('Current directory is %s' % os.getcwd())


def choose_notify_function(method):
    "Return a function used to notify"
    if method == 'email':
        return lambda mail, text: send_email(recipients=[mail],
                                             subject='space status', body=text)
    elif method == 'print':
        return print  # the print function


def check_periodically(interval, throttle_days, warning_level, notify):
    "Check status of the machines every interval seconds, notify if necessary"
    s_per_day = 60 * 60 * 24  # seconds in a day

    logging.debug('Getting initial status...')
    try:
        last_status = load_last_status()
    except Exception:  # anyone, really, just be robust
        last_status = get_status(warning_level)

    while True:
        logging.debug('Checking space status...')
        status = get_status(warning_level)
        for space in status:
            if (status[space] != last_status[space] or
                (status[space] == 'warn' and
                 time.time() - last_notification_time[space] > throttle_days * s_per_day)):
                if status[space] != last_status[space]:
                    logging.warn('Changes found in space "%s". Notifying.' % space)
                else:
                    logging.warn('Unreported warning in space "%s". Notifying.' % space)
                notify(mails_all[space], describe(space, status[space], last_status[space]))
                last_notification_time[space] = time.time()
            else:
                logging.debug('Nothing to report on space "%s".' % space)
        last_status = status
        save_status(status)
        time.sleep(interval)


def get_status(warning_level):
    "Return dict with dataset/user and its status (ok, warn, undefined)"
    # ok if less than 80% of space used, warn if more.
    status = {}
    for dataset, ratio in get_ratio_datasets().items():
        if dataset in datasets:
            status[dataset] = 'ok' if ratio < warning_level else 'warn'
    for user in users:
        try:
            status[user] = 'ok' if get_ratio_user(user) < warning_level else 'warn'
        except ZeroDivisionError:
            status[user] = 'undefined'
    return status


def get_ratio_datasets():
    "Return dict with the used/total space for all datasets"
    ratios = {}
    for line in run(['zfs', 'list', '-Hp']).splitlines():
        dataset, used, available = line.split()[:3]
        if dataset.startswith('pool_cnb/'):
            ratios[dataset[9:]] = int(used) / (int(used) + int(available))
    return ratios


def get_ratio_user(user):
    "Return used/quota ratio for the given user"
    def get(field):
        args = ['-Hp', 'user%s@%s' % (field, user), ZFS_DATASET]
        return int(run(['zfs', 'get'] + args).split()[2])
    try:
        return get('used') / get('quota')
    except ValueError as e:
        logging.error('%s - Maybe you not running as root?' % e)
        sys.exit('Unrecoverable error. Please check the log file.')


def run(command):
    logging.debug('Running: %s' % ' '.join(command))
    return sp.check_output(command, universal_newlines=True)


def describe(space, status, last_status):
    "Return a text explaining the status"
    return """\
Hello,

This is a friendly warning about the usage of space "%s".

  Previous status: %s
  Current status: %s

If you are using too much space, please consider freeing some of it or asking for
more space before it's too late.

If you receive this mail because your usage went back to normal, congratulations,
enjoy it.

Sincerely,
  The space monitor
    """ % (space, last_status, status)


def send_email(recipients, subject, body):
    "Send email to recipients with the given subject and body text"
    sp.call(['sendEmail', '-s', 'smtp.gmail.com:587', '-o', 'tls=yes',
             '-xu', EMAIL_USER, '-xp', EMAIL_PASSWD,
             '-f', EMAIL_USER, '-u', subject, '-m', body] +
            ['-t'] + recipients, stdout=sp.DEVNULL, stderr=sp.DEVNULL)


def save_status(status):
    "Save the given status to disk"
    with open(STATUSFILE, 'wt') as f:
        for m, s in status.items():
            f.write('%s %s\n' % (s, m))


def load_last_status():
    "Return status as loaded from disk"
    status = {}
    for line in open(STATUSFILE):
        s, m = line.strip().split(' ', 1)
        status[m] = s
    return status



if __name__ == '__main__':
    main()
