#!/usr/bin/env python3

"""
Alert whenever more than 80% of the quota (or available space) is used.
"""

# ZFS concepts:
# https://en.wikipedia.org/wiki/ZFS#Terminology_and_storage_structure
#
# We want to watch out the space being used in the different
# "datasets" defined (in zfs terminology, a dataset is a file
# system). In addition to checking on the space used by datasets (zfs
# list), we want to check on the user quotas within the
# pool_cnb/bioinfo dataset (zfs get userquota@user pool_cnb/bioinfo).

import sys
import os
import time
import logging
import subprocess as sp
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
from configparser import ConfigParser, ParsingError

import daemonize

PATH = os.path.dirname(os.path.realpath(__file__))
LOGFILE = os.path.join(PATH, 'space_monitor.log')
STATUSFILE = os.path.join(PATH, 'last_space_status.txt')

TRIGGER_FRACTION = 0.80  # if more used, we start pestering


def main():
    args = parse_arguments()
    auth, datasets, users, emails = read_config(args.config)

    if not args.no_daemon:
        print('Becoming a daemon. For more info check: %s' % LOGFILE)
        daemonize.daemonize()
    start_logging(args.logfile, args.loglevel)
    notify = choose_notify_function(args.notify, emails, auth)
    check_periodically(args.interval, args.reminder_days,
                       notify, datasets, users)


def parse_arguments():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('--no-daemon', action='store_true', help='keep attached to the console')
    add('--logfile', default=LOGFILE, help='path of the file with the logs')
    add('--loglevel', choices=['error', 'warning', 'info', 'debug'],
        default='warning', help='logger verbosity level')
    add('--reminder-days', default=7, help='number of days between reminders')
    add('--notify', choices=['email', 'print'], default='email',
        help='method used for notification')
    add('--interval', type=int, default=60, help='time (in s) between checks')
    add('--config', default='space_monitor.cfg',
        help='file with auth, datasets and users configuration')
    return parser.parse_args()


def read_config(fname):
    "Return parameters read from configuration file fname"
    print('Reading config file %s ...' % fname)
    cp = ConfigParser()
    try:
        cp.read_file(open(fname))
        for section in ['auth', 'datasets', 'users']:
            assert section in cp, 'Missing section [%s]' % section
        for x in ['mail', 'password']:
            assert x in cp['auth'], 'Missing field "%s" in section [auth]' % x
    except (FileNotFoundError, AssertionError,
            ValueError, ParsingError) as e:
        sys.exit('Error in file %s: %s' % (fname, e))

    auth = cp['auth']
    datasets = list(cp['datasets'].keys())
    users = list(cp['users'].keys())
    emails = {space: email for space, email in
              list(cp['datasets'].items()) + list(cp['users'].items())}
    return auth, datasets, users, emails


def start_logging(logfile, loglevel):
    level = {'error': 40, 'warning': 30, 'info': 20, 'debug': 10}[loglevel]
    logging.basicConfig(filename=logfile, level=level,
                        format='%(asctime)s [%(levelname)s] %(message)s')
    logging.info('Starting.')
    logging.debug('Current directory is %s' % os.getcwd())


def choose_notify_function(method, emails, auth_config):
    "Return a function used to notify"
    if method == 'email':
        def notify_by_email(space, status_new, status_old):
            subject = 'Space at %s: %s' % (os.uname().nodename, status_new)
            text = describe(space, status_new, status_old)
            send_email([emails[space]], subject, text, auth_config)
        return notify_by_email
    elif method == 'print':
        return print  # the print function


def check_periodically(interval, reminder_days, notify, datasets, users):
    "Check status of the machines every interval seconds, notify if necessary"
    t_reminder = reminder_days * (60 * 60 * 24)  # in seconds

    spaces = datasets + users

    last_status = get_last_status()
    for space in set(spaces) - set(last_status.keys()):
        logging.warning('Space "%s" was not in last status.' % space)
        last_status[space] = 'ok'

    last_notification_time = {space: 0 for space in spaces}

    while True:
        logging.debug('Checking space status...')
        status = get_status(datasets, users)
        for space in spaces:
            status_new, status_old = status[space], last_status[space]
            dt = time.time() - last_notification_time[space]
            if alert(space, status_new, status_old, remind=(dt > t_reminder)):
                notify(space, status_new, status_old)
                last_notification_time[space] = time.time()
        last_status = status
        save_status(status)
        time.sleep(interval)


def get_last_status():
    logging.debug('Getting initial status...')
    try:
        return load_last_status()
    except Exception as e:  # anyone, really, just be robust
        logging.info('Could not read last status: %s' % e)
        return {}


def load_last_status():
    "Return status as loaded from disk"
    status = {}
    for line in open(STATUSFILE):
        s, m = line.strip().split(' ', 1)
        status[m] = s
    return status


def save_status(status):
    "Save the given status to disk"
    with open(STATUSFILE, 'wt') as f:
        for m, s in status.items():
            f.write('%s %s\n' % (s, m))


def alert(space, status_new, status_old, remind):
    "Return True if the status of the space requires a notification"
    if status_new == status_old != 'warn':
        logging.debug('Nothing to report on space "%s".' % space)
        return False
    elif status_new != status_old:
        logging.warn('Changes found in space "%s". Notifying.' % space)
        return True
    elif status_new == 'warn' and remind:
        logging.warn('Error persists in space "%s". Notifying.' % space)
        return True
    else:
        logging.debug('Status of space "%s": %s' % (space, status_new))
        return False


def get_status(datasets, users):
    "Return dict with dataset/user and its status (ok, warn, undefined)"
    # ok if less than 80% of space used, warn if more.
    status = {}
    for dataset, ratio in get_ratio_datasets().items():
        if dataset in datasets:
            status[dataset] = 'ok' if ratio < TRIGGER_FRACTION else 'warn'
    for user in users:
        try:
            status[user] = ('ok' if get_ratio_user(user) < TRIGGER_FRACTION
                            else 'warn')
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
        args = ['-Hp', 'user%s@%s' % (field, user), 'pool_cnb/bioinfo']
        return int(run(['zfs', 'get'] + args).split()[2])
    try:
        return get('used') / get('quota')
    except ValueError as e:
        logging.error('%s - Maybe you are not running as root?' % e)
        sys.exit('Unrecoverable error. Please check the log file.')


def run(command):
    logging.debug('Running: %s' % ' '.join(command))
    return sp.check_output(command, universal_newlines=True)


def describe(space, status_new, status_old):
    "Return a text explaining the status"
    too_much = ('You seem to be using too much space, please consider freeing '
                'some of it or asking for more space before it is too late.')
    all_cool = ('You received this mail because your usage went back to normal. '
                'Congratulations, enjoy it.')
    return """\
Hello,

This message concerns the usage of space "%s".

  Previous status: %s
  Current status: %s

%s

Sincerely,
  The space monitor at %s
    """ % (space, status_old, status_new,
           too_much if status_new == 'warn' else all_cool,
           os.uname().nodename)


def send_email(recipients, subject, body, auth_config):
    "Send email to recipients with the given subject and body text"
    sp.call(['sendEmail', '-s', 'smtp.gmail.com:587', '-o', 'tls=yes',
             '-xu', auth_config['mail'], '-xp', auth_config['password'],
             '-f', auth_config['mail'], '-u', subject, '-m', body] +
            ['-t'] + recipients, stdout=sp.DEVNULL, stderr=sp.DEVNULL)



if __name__ == '__main__':
    main()
