#!/usr/bin/env python3

"""
Like cat on steroids to manipulate json files.

It can read json from a file (even if it's a zip file) or from stdin,
filter the different parts (letting only elements in them whose selected
field matches the given regular expression), and compact the output.

It can be handy for example to manipulate metadata exported from dhis2,
so it can be later on imported in another instance.
"""

import sys
import re
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
import zipfile

INDENT_STEP = 2


def main():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('file', nargs='?', help='input file (read from stdin if not given)')
    add('-o', '--output', help='output file (write to stdout if not given')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--filters', nargs='+',
                       help='part:field:regexp selection filters')
    group.add_argument('--filters-file', help='file with selection patterns')
    add('-q', '--quick', action='store_true', help='skip paranoid steps')
    add('-c', '--compact', action='store_true', help='output a compacted json')
    args = parser.parse_args()

    if args.filters:
        filters = [f.split(':', 2) for f in args.filters]
    elif args.filters_file:
        filters = read_filters(args.filters_file)
    else:
        filters = []

    text = zread(args.file)

    if not args.quick:
        text = compact(text)

    text = expand(text)
    for part, field, regexp in filters:
        text = filter_parts(text, part, field, regexp)
    if args.compact:
        text = compact(text)

    if args.output:
        with open(args.output, 'wt') as fout:
            fout.write(text)
    else:
        print(text, end='')


def read_filters(fname):
    "Return list of filters [(part, field, regexp), ...] from file fname"
    filters = []
    for line_dirty in open(fname):
        line = line_dirty.strip()
        if line and not line.startswith('#'):
            filters.append(line.split(':', 2))
    return filters


def zread(fname):
    "Return contents of file, which works also for single zip files"
    if not fname:
        return sys.stdin.read()
    elif zipfile.is_zipfile(fname):
        zf = zipfile.ZipFile(fname)
        assert len(zf.filelist) == 1, \
            'zip file "%s" should contain only one file' % fname
        return zf.open(zf.filelist[0]).read().decode('utf8')
    else:
        return open(fname).read()


def filter_parts(text, part, field, regexp):
    "Return a json text with only the elements that match regexp"
    # For the given field in the given part.
    # The text must be an expanded json.
    text_filtered = ''
    indent = 0
    in_part = False
    current_region = ''
    current_field = ''
    for line in text.splitlines():
        if not in_part and line.lstrip().startswith('"%s":' % part):  # start
            in_part = True
            indent = len(line) - len(line.lstrip())
            text_filtered += line + '\n'
        elif not in_part:
            text_filtered += line + '\n'
        elif len(line) - len(line.lstrip()) <= indent:  # end
            text_filtered += line + '\n'
            in_part = False
        elif line.startswith(' ' * (indent + INDENT_STEP) + '}'):
            # we could read the step from the indentation of the second line...
            current_region += line + '\n'
            if re.search(regexp, current_field):
                text_filtered += current_region
            current_region = ''
            current_field = ''
        elif line.lstrip().startswith('"%s":' % field):
            current_region += line + '\n'
            current_field = line.split('"')[3]
        else:
            current_region += line + '\n'

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
            text_nice += '\n' + ' ' * INDENT_STEP * indent_level

        text_nice += c

        if c == ',' and not in_string:
            text_nice += '\n' + ' ' * INDENT_STEP * indent_level
        if c in '{[' and not in_string:
            indent_level += 1
            text_nice += '\n' + ' ' * INDENT_STEP * indent_level
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
