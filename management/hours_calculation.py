#!/usr/bin/env python

"""
Calculation of personnel hours
"""

import sys
import os
import argparse
from colorama import Fore
from colorama import Style

COLOR = True
price = 0.0
hours = []

def main():
    global COLOR

    args = get_args()

    if args.price == 0.0:
        print 'ERROR: slaves are forbidden, please pay them something different from zero'
        return
    else: 
        price = args.price
    hours = args.hours

    if args.no_color or not os.isatty(sys.stdout.fileno()):
        COLOR = False

    if args.extra:
        extra = args.extra

    print_invoice(args.price, args.hours, args.extra)


def get_args():
    "Return arguments"
    parser = argparse.ArgumentParser(description=__doc__)
    add = parser.add_argument  # shortcut
    add('--price', type=int, action='store', help="hourly rate")
    add('--hours', type=float, default=[], nargs='+', help="hours dedicated per month")
    add('--extra', type=float, default=0.0, help="extra expenses (platzi)")
    add('--no-color', action='store_true', help="don't use colored output")
    return parser.parse_args()


def print_invoice(price, hours, extra=0.0):
    print '-----------'
    print 'Hourly rate: %s' % price
    print 'Total hours: %s' % sum(hours)
    print 'Total cost: %s' % (sum(hours)*price+extra)
    print '-----------'
    print 'Detail:'

    total = 0.0
    for hour in hours:
        subtotal = hour*price
        print 'time: %s - price: %s' % (hour, subtotal)
        total += subtotal

    print 'Extra: %s' % extra
    total += extra
    out = 'TOTAL: %s' % total
    print (green(out) if COLOR else out)
    print '-----------'
    print ''
    return 

def magenta(txt):
    return '\x1b[35m%s\x1b[0m' % txt

def green(txt):
    return '\x1b[42m%s\x1b[0m' % txt

def red(txt):
    return '\x1b[31m%s\x1b[0m' % txt

if __name__ == '__main__':
    main()
