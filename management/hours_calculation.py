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
irpf = 15.0
iva = 21.0

def main():
    global COLOR
    global irpf
    global iva

    args = get_args()
    hours = args.hours
    price = 0.0
    irpf = args.irpf
    iva = args.iva

    if 0.0 in args.price:
        print('ERROR: slaves are forbidden, please pay them something different from zero')
        return
    else: 
        price = args.price


    if args.no_color or not os.isatty(sys.stdout.fileno()):
        COLOR = False

    if args.extra:
        extra = args.extra

    print_invoice(args.price, args.hours, args.extra)


def get_args():
    "Return arguments"
    parser = argparse.ArgumentParser(description=__doc__)
    add = parser.add_argument  # shortcut
    add('--price', type=int, action='store', nargs='+', help="hourly rate (can be single value or one per hour entry)")
    add('--hours', type=float, default=[], nargs='+', help="hours dedicated per month")
    add('--extra', type=float, default=0.0, help="extra expenses (platzi)")
    add('--no-color', action='store_true', help="don't use colored output")
    add('--irpf', type=float, action='store', default=15.0, help="IRPF deduction in percentage")
    add('--iva', type=float, action='store', default=21.0, help="IVA in percentage")
    return parser.parse_args()


def print_invoice(prices, hours, extra=0.0):
    if len(prices) == 1:
        prices = [prices[0] for i in range(len(hours))]
    elif len(prices) != len(hours):
        print('ERROR: price can only be size 1 or hours size')

    print('-----------')
    print('Hourly rate(s): %s' % prices)
    print('Total hours: %s' % sum(hours))
    print('Total cost: %s' % (sum([hour * price for hour,price in zip(hours,prices)])+extra))
    print('-----------')
    print('Detail:')

    total = 0.0
    for hour,price in zip(hours,prices):
        subtotal = hour * price
        print('time: %s - price: %s' % (hour, subtotal))
        total += subtotal

    print('Extra: %s' % extra)
    total += extra
    base = total
    print('Base: %s' % total)
    irpf_total = base * irpf / 100.0
    iva_total = base * iva / 100.0
    irpf_text = 'IRPF: -%s' % irpf_total
    print(red(irpf_text) if COLOR else irpf_text)
    print('IVA: %s' % iva_total)
    total += iva_total
    total -= irpf_total
    out = 'TOTAL: %s' % total
    print (green(out) if COLOR else out)
    print ('-----------')
    print ('')
    return 

def magenta(txt):
    return '\x1b[35m%s\x1b[0m' % txt

def green(txt):
    return '\x1b[42m%s\x1b[0m' % txt

def red(txt):
    return '\x1b[31m%s\x1b[0m' % txt

if __name__ == '__main__':
    main()
