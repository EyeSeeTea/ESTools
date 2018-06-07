#!/usr/bin/env python3

"""
Functions to manipulate the jsons that come from the dhis2
import/export app.
"""

import sys
import re
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt


def main():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('-i', '--file', help='input file (read from stdin if not given)')
    add('-o', '--output', help='output file (write to stdout if not given')
    add('action', choices=['read', 'expand', 'compact', 'filter-indicators'],
        help='action to perform on the file')
    add('--regexp', default='^HEP_', help='regexp to use when filtering')
    args = parser.parse_args()

    text = (open(args.file) if args.file else sys.stdin).read()

    fout = open(args.output, 'wt') if args.output else sys.stdout

    action = {
        'read': lambda txt: txt,
        'expand': expand,
        'compact': compact,
        'filter-indicators': lambda txt: filter_indicators(txt, args.regexp),
    }[args.action]

    fout.write(action(text))


def filter_indicators(text, regexp):
    "Return only the indicators whose name match the given regexp"
    # The text must be an expanded json.
    text_filtered = ''
    indent = 0
    in_indicators = False
    current_indicator = ''
    current_name = ''
    for line in text.splitlines():
        # Find the start of the indicators.
        if not in_indicators and line.lstrip().startswith('"indicators":'):
            in_indicators = True
            indent = len(line) - len(line.lstrip())
            text_filtered += line + '\n'
            continue

        # Find the end of the indicators, and stop processing.
        if in_indicators and len(line) - len(line.lstrip()) <= indent:
            in_indicators = False

        if not in_indicators:
            text_filtered += line + '\n'
            continue

        current_indicator += line + '\n'

        if line.lstrip().startswith('"name":'):
            current_name = line.split('"')[3]

        if line.startswith(' ' * (indent + 2) + '}'):  # end of indicator
            if re.search(regexp, current_name):
                text_filtered += current_indicator
            current_indicator = ''
    return text_filtered


def expand(text):
    "Return a readable version of a compacted json text"
    text_nice = ''
    indent_level = 0
    in_string = False
    last_c = ''
    for c in text:
        assert c != ' ' or in_string, 'Not a compacted json'

        if c == '"' and last_c != '\\':
            in_string = not in_string

        if c in '}]' and not in_string:
            indent_level -= 1
            text_nice += '\n' + ' ' * 2 * indent_level

        text_nice += c

        if c == ',' and not in_string:
            text_nice += '\n' + ' ' * 2 * indent_level
        if c in '{[' and not in_string:
            indent_level += 1
            text_nice += '\n' + ' ' * 2 * indent_level
        last_c = c
    return text_nice


def compact(text):
    "Return a compacted json"
    text_compact = ''
    in_string = False
    last_c = ''
    for c in text:
        if c == '"' and last_c != '\\':
            in_string = not in_string
        if c not in '\n ' or in_string:
            text_compact += c
        last_c = c
    return text_compact



if __name__ == '__main__':
    main()
