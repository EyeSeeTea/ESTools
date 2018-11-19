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
import json
import subprocess as sp
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
from configparser import ConfigParser, ParsingError

PATH = os.path.dirname(os.path.realpath(__file__))
SAVED_DATA_FILE = os.path.join(PATH, 'space_monitor_saved_data.json')

TRIGGER_FRACTION = 0.80  # if more used, we start pestering


def main():
    args = parse_arguments()
    mail_config, datasets, users, emails = read_config(args.config)

    notify = choose_notify_function(args.notify, emails, mail_config)

    check(datasets, users, notify, args.reminder_days)


def parse_arguments():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('--reminder-days', default=7, help='number of days between reminders')
    add('--notify', choices=['email', 'print'], default='email',
        help='method used for notification')
    add('--config', default='space_monitor.cfg',
        help='file with auth, datasets and users configuration')
    return parser.parse_args()


def read_config(fname):
    "Return parameters read from configuration file fname"
    print('Reading config file %s ...' % fname)
    cp = ConfigParser()
    try:
        cp.read_file(open(fname))
        for section in ['mail', 'datasets', 'users']:
            assert section in cp, 'Missing section [%s]' % section
        for x in ['from', 'password', 'cc']:
            assert x in cp['mail'], 'Missing field "%s" in section [mail]' % x
    except (FileNotFoundError, AssertionError,
            ValueError, ParsingError) as e:
        sys.exit('Error in file %s: %s' % (fname, e))

    mail_config = cp['mail']
    datasets = list(cp['datasets'].keys())
    users = list(cp['users'].keys())
    emails = {space: emails.split() for space, emails in
              list(cp['datasets'].items()) + list(cp['users'].items())}
    return mail_config, datasets, users, emails


def choose_notify_function(method, emails, mail_config):
    "Return a function used to notify"
    if method == 'email':
        def notify_by_email(space, status_new, status_old):
            subject = 'Space at %s: %s' % (os.uname().nodename, status_new)
            text = describe(space, status_new, status_old)
            send_email(emails[space], subject, text, mail_config)
        return notify_by_email
    elif method == 'print':
        return print  # the print function (useful for debugging)


def check(datasets, users, notify, reminder_days):
    "Check status of the machines, notify if necessary"
    t_reminder = reminder_days * (60 * 60 * 24)  # in seconds

    spaces = datasets + users

    last_status, last_notification_time = load_data()
    fill_missing_data(last_status, last_notification_time, spaces)

    status = get_status(datasets, users)

    unknown_spaces = set(spaces) - set(status.keys())
    if unknown_spaces:
        sys.exit('Error: Unknown spaces: %s' % ' '.join(unknown_spaces))

    for space in spaces:
        status_new, status_old = status[space], last_status[space]
        dt = time.time() - last_notification_time[space]
        if alert(space, status_new, status_old, remind=(dt > t_reminder)):
            notify(space, status_new, status_old)
            last_notification_time[space] = time.time()

    save_data(status, last_notification_time)


def load_data():
    "Return last_status, last_notification_time as loaded from disk"
    print('Loading saved data...')
    try:
        with open(SAVED_DATA_FILE) as f:
            last_status, last_notification_time = json.load(f)
            assert all(is_valid_status(s) for s in last_status.values())
            t_now = time.time()
            assert all(t < t_now for t in last_notification_time.values())
            return last_status, last_notification_time
    except Exception as e:  # anyone, really, just be robust
        print('Warning: problem reading saved data, will reset: %s' % e)
        return {}, {}


def is_valid_status(status):
    return status in ['ok', 'warn', 'undefined']


def fill_missing_data(last_status, last_notification_time, spaces):
    "Put default values for status and times of spaces that don't have them set"
    for space in set(spaces) - set(last_status.keys()):
        print('Setting status for space %s' % space)
        last_status[space] = 'ok'
    for space in set(spaces) - set(last_notification_time.keys()):
        print('Setting last notification time for space %s' % space)
        last_notification_time[space] = 0.0


def save_data(status, last_notification_time):
    "Save status and last_notification_time to disk in json format"
    with open(SAVED_DATA_FILE, 'wt') as f:
        json.dump([status, last_notification_time], f, indent=True)


def alert(space, status_new, status_old, remind):
    "Return True if the status of the space requires a notification"
    if status_new != 'warn' and status_old != 'warn':
        print('Status of space "%s": %s (no report)' % (space, status_new))
        return False
    elif status_new == status_old == 'warn':
        if remind:  # redundant for clarity
            print('Warning: Error persists in space "%s". Notifying.' % space)
            return True
        else:
            print('Warning: Error persists in space "%s" (no report).' % space)
            return False
    else:
        print('Warning: Changes found in space "%s". Notifying.' % space)
        return True


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
        sys.exit('Error: %s - Maybe you are not running as root?' % e)


def run(command):
    print('Running: %s' % ' '.join(command))
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


def send_email(recipients, subject, body, mail_config):
    "Send email to recipients with the given subject and body text"
    cc = mail_config['cc'].split()
    to = ['-t'] + recipients + ((['-cc'] + cc) if cc else [])
    sp.call(['sendEmail', '-s', 'smtp.gmail.com:587', '-o', 'tls=yes',
             '-xu', mail_config['from'], '-xp', mail_config['password'],
             '-f', mail_config['from'], '-u', subject, '-m', body] + to,
            stdout=sp.DEVNULL, stderr=sp.DEVNULL)



if __name__ == '__main__':
    main()
