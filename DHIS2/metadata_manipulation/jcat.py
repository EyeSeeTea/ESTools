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
from argparse import ArgumentParser, RawDescriptionHelpFormatter as fmt
import zipfile

INDENT_STEP = 2


def main():
    args = get_args()

    text = read(args.file)
    text = expand(compact(text))  # normalize spacing

    filters = get_filters(args.filters, args.filters_file)
    text = apply_filters(text, filters, args.multi)

    if args.compact:
        text = compact(text)

    write(args.output, text)


def get_args():
    "Parse command-line arguments and return them"
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('file', nargs='?', help='input file (read from stdin if not given)')
    add('-o', '--output', help='output file (write to stdout if not given')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--filters', nargs='+', metavar='FILTER',
                       help='part:field:regexp selection filters')
    group.add_argument('--filters-file', help='file with selection patterns')
    add('-m', '--multi', action='store_true',
        help='allow multiple matches for field (uses the last match)')
    add('-c', '--compact', action='store_true', help='output a compacted json')
    return parser.parse_args()


def get_filters(filters_expressions, filters_file):
    "Return list of filters [(part, field, regexp), ...]"
    if filters_expressions:
        return [f.split(':', 2) for f in filters_expressions]
    elif filters_file:
        return read_filters(filters_file)
    else:
        return []


def read_filters(fname):
    "Return list of filters [(part, field, regexp), ...] from file fname"
    filters = []
    for line_dirty in open(fname):
        line = line_dirty.strip()
        if line and not line.startswith('#'):
            filters.append(line.split(':', 2))
    return filters


def read(fname):
    "Return contents of file, which works also for single zip files"
    if not fname:
        try:
            return sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(130)  # same as cat
    elif zipfile.is_zipfile(fname):
        zf = zipfile.ZipFile(fname)
        assert len(zf.filelist) == 1, \
            'Zip file "%s" should contain only one file' % fname
        with zf.open(zf.filelist[0]) as fin:
            return fin.read().decode('utf8')
    else:
        with open(fname) as fin:
            return fin.read()


def write(fname, text):
    if fname:
        with open(fname, 'wt') as fout:
            fout.write(text)
    else:
        print(text, end='')


def apply_filters(text, filters, multi):
    for part, field, regexp in filters:
        text = filter_parts(text, part, field, regexp, multi)
    return text


def filter_parts(text, part, field, regexp, multi=False):
    "Return a json text with only the elements that match regexp"
    # For the given field in the given part.
    # The text must be an expanded json.
    text_filtered = ''
    indent = 0  # indentation level of the part we will filter
    in_part = False  # are we in the part we want to filter?
    current_region = ''  # region we are scanning and may not include
    current_field = ''  # field that is being defined (like "name":...)
    just_filtered = False  # did we just filter out something?
    for line in text.splitlines():
        if not in_part:
            if line.startswith(' ' * INDENT_STEP + '"%s":' % part):  # start
                in_part = True
                indent = len(line) - len(line.lstrip())
            just_filtered = False
            text_filtered += line + '\n'
        elif len(line) - len(line.lstrip()) <= indent:  # end part
            if just_filtered and text_filtered[-2] == ',':
                text_filtered = text_filtered[:-2] + '\n'
            just_filtered = False
            text_filtered += line + '\n'
            in_part = False
        elif line.startswith(' ' * (indent + INDENT_STEP) + '}'):  # end region
            current_region += line + '\n'
            if re.search(regexp, current_field):
                text_filtered += current_region
                just_filtered = False
            else:
                just_filtered = True
            current_region = ''
            current_field = ''
        elif line.lstrip().startswith('"%s":' % field):  # find field
            current_region += line + '\n'
            if not multi and current_field != '':
                sys.exit('Error: multiple fields named "%s" in %s (run with '
                         '--multi to allow for it)' % (field, part))
            current_field = line.split('"')[3]  #   "field_name":"field_value"
            just_filtered = False
        else:  # keep adding to region
            current_region += line + '\n'
            just_filtered = False

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
            text_nice = text_nice.rstrip()
            text_nice += '\n' + ' ' * INDENT_STEP * indent_level

        text_nice += c

        if c == ',' and not in_string:
            text_nice += '\n' + ' ' * INDENT_STEP * indent_level
        if c in '{[' and not in_string:
            indent_level += 1
            text_nice += '\n' + ' ' * INDENT_STEP * indent_level
        last_c = c
    return text_nice + '\n'


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