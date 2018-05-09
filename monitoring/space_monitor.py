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
from configparser import ConfigParser, ParsingError

import daemonize

PATH = os.path.dirname(os.path.realpath(__file__))
LOGFILE = os.path.join(PATH, 'space_monitor.log')
STATUSFILE = os.path.join(PATH, 'last_space_status.txt')

TRIGGER_FRACTION = 0.80  # if more used, we start pestering

last_notification_time = {}


def main():
    args = parse_arguments()
    cfg = read_config(args.config)

    if not args.no_daemon:
        daemonize.daemonize()
    start_logging(args.logfile, args.loglevel)
    notify = choose_notify_function(args.notify, cfg['auth'])
    check_periodically(args.interval, args.throttle_days, args.warning_level,
                       notify, cfg['datasets'], cfg['users'])


def parse_arguments():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('--no-daemon', action='store_true', help='keep attached to the console')
    add('--logfile', default=LOGFILE, help='path of the file with the logs')
    add('--loglevel', default=logging.DEBUG, help='logger verbosity level')
    add('--throttle-days', default=7, help='number of days between reminders')
    add('--notify', choices=['email', 'print'], default='email',
        help='method used for notification')
    add('--interval', type=int, default=60, help='time (in s) between checks')
    add('--config', default='space_monitor.cfg',
        help='file with auth, datasets and users configuration')
    return parser.parse_args()


def read_config(fname):
    "Return parser with the parameters read from configuration file fname"
    logging.info('Reading config file %s ...' % fname)
    cp = ConfigParser()
    try:
        cp.read_file(open(fname))
        for section in ['auth', 'datasets', 'users']:
            assert section in cp, 'Missing section [%s]' % section
    except (FileNotFoundError, AssertionError,
            ValueError, ParsingError) as e:
        sys.exit('Error in file %s: %s' % (fname, e))
    return cp


def start_logging(logfile, loglevel):
    logging.basicConfig(filename=logfile, level=loglevel,
                        format='%(asctime)s [%(levelname)s] %(message)s')
    logging.info('Starting.')
    logging.debug('Current directory is %s' % os.getcwd())


def choose_notify_function(method, auth_config):
    "Return a function used to notify"
    if method == 'email':
        return lambda recipient, text: send_email([recipient], 'space status',
                                                  text, auth_config)
    elif method == 'print':
        return print  # the print function


def check_periodically(interval, throttle_days, notify, datasets, users):
    "Check status of the machines every interval seconds, notify if necessary"
    s_per_day = 60 * 60 * 24  # seconds in a day

    logging.debug('Getting initial status...')
    try:
        last_status = load_last_status()
    except Exception as e:  # anyone, really, just be robust
        logging.info('Could not read last status: %s' % e)
        last_status = get_status(datasets, users)

    last_notification_time = {space: 0 for space in last_status}

    while True:
        logging.debug('Checking space status...')
        status = get_status()
        for space in status:
            dt = time.time() - last_notification_time[space]
            if (status[space] != last_status[space] or
                (status[space] == 'warn' and dt > throttle_days * s_per_day)):
                if status[space] != last_status[space]:
                    logging.warn('Changes found in space "%s". Notifying.'
                                 % space)
                else:
                    logging.warn('Unreported warning in space "%s". Notifying.'
                                 % space)
                notify(mails_all[space], describe(space, status[space],
                                                  last_status[space]))
                last_notification_time[space] = time.time()
            else:
                logging.debug('Nothing to report on space "%s".' % space)
        last_status = status
        save_status(status)
        time.sleep(interval)


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

If you are using too much space, please consider freeing some of it or asking
for more space before it's too late.

If you receive this mail because your usage went back to normal,
congratulations, enjoy it.

Sincerely,
  The space monitor
    """ % (space, last_status, status)


def send_email(recipients, subject, body, auth_config):
    "Send email to recipients with the given subject and body text"
    sp.call(['sendEmail', '-s', 'smtp.gmail.com:587', '-o', 'tls=yes',
             '-xu', auth_config['user'], '-xp', auth_config['password'],
             '-f', auth_config['user'], '-u', subject, '-m', body] +
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
