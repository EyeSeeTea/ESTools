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
from collections import namedtuple
from argparse import ArgumentParser, RawDescriptionHelpFormatter as fmt
import zipfile

Filter = namedtuple('Filter', ['nesting', 'part', 'field', 'regexp'])

INDENT_STEP = 2


def main():
    args = get_args()

    text = read(args.file)
    text = expand(compact(text))  # normalize spacing

    text = apply_replacements(text, args.replacements)

    if args.selections:
        text = select(text, args.selections)

    filters = get_filters(args.filters, args.filters_file)
    text = apply_filters(text, filters, args.multi)

    if args.sort:
        text = jsort(text)

    if args.compact:
        text = compact(text)

    write(args.output, text)


def get_args():
    "Parse command-line arguments and return them"
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('file', nargs='?', help='input file (read from stdin if not given)')
    add('-o', '--output', help='output file (write to stdout if not given')
    add('--replacements', nargs='+', metavar='FROM TO', default=[],
        help='text to replace')
    add('--selections', nargs='+', metavar='SECTION', help='sections to select')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--filters', nargs='+', metavar='FILTER',
                       help='::...:part:field:regexp selection filters')
    group.add_argument('--filters-file', help='file with selection patterns')
    add('-m', '--multi', action='store_true',
        help='allow multiple matches for field (uses the last match)')
    add('-c', '--compact', action='store_true', help='output a compacted json')
    add('-s', '--sort', action='store_true', help='output a sorted json')
    args = parser.parse_args()

    if file_arg_maybe_misplaced(args.file, args.filters):
        print('Warning: no file given, but one of the filters looks '
              'like a filename.')

    return args


def file_arg_maybe_misplaced(fname, filters):
    return not fname and filters and not all(':' in x for x in filters)


def apply_replacements(text, replacements):
    "Return text with all the pairs of FROM TO replacements applied"
    n = len(replacements)
    if n % 2 != 0:
        sys.exit('Error: uneven number of replacements (%d), but replacements '
                 'should come in pairs (from, to)' % n)
    pairs = [(replacements[2 * i], replacements[2 * i + 1]) for i in range(n // 2)]
    for x, y in pairs:
        text = text.replace(x, y)
    return text


def get_filters(filters_expressions, filters_file):
    "Return list of filters [(nesting, part, field, regexp), ...]"
    if filters_expressions:
        return [decode_filter(f) for f in filters_expressions]
    elif filters_file:
        return read_filters(filters_file)
    else:
        return []


def decode_filter(expression):
    "Return a Filter tuple from an expression like ::...:part:field:regexp"
    expression_stripped = expression.lstrip(':')
    nesting = len(expression) - len(expression_stripped) + 1
    part, field, regexp = expression_stripped.split(':', 2)
    return Filter(nesting, part, field, regexp)


def read_filters(fname):
    "Return list of filters [(part, field, regexp), ...] from file fname"
    filters = []
    for line_dirty in open(fname):
        line = line_dirty.strip()
        if line and not line.startswith('#'):
            filters.append(decode_filter(line))
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


def select(text, selections):
    "Return a json text with only the sections that appear in selections"
    text_selected = '{\n'
    current_section = ''
    for line in text.splitlines():
        if line.startswith(' ' * INDENT_STEP + '"'):
            current_section = line.split('"', 2)[1]

        if current_section in selections:
            text_selected += line + '\n'

    text_selected += '}\n'

    if text_selected.endswith(',\n}\n'):
        text_selected = text_selected[:-4] + '\n}\n'

    return text_selected


def apply_filters(text, filters, multi):
    for jfilter in filters:
        text = filter_parts(text, jfilter, multi)
    return text


def filter_parts(text, jfilter, multi=False):
    "Return a json text with only the elements that pass the jfilter filter"
    # That is, that match the regexp for the given field in the given part.
    # The text must be an expanded json.
    text_filtered = ''
    indent = 0  # indentation level of the part we will filter
    in_part = False  # are we in the part we want to filter?
    current_region = ''  # region we are scanning and may not include
    current_field = ''  # field that is being defined (like "name":...)
    just_filtered = False  # did we just filter out something?
    for line in text.splitlines():
        if not in_part:
            spaces = ' ' * INDENT_STEP * jfilter.nesting
            if line.startswith('%s"%s":' % (spaces, jfilter.part)):  # start
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
            if re.search(jfilter.regexp, current_field):
                text_filtered += current_region
                just_filtered = False
            else:
                just_filtered = True
            current_region = ''
            current_field = ''
        elif line.lstrip().startswith('"%s":' % jfilter.field):  # find field
            current_region += line + '\n'
            if not multi and current_field != '':
                sys.exit('Error: multiple fields named "%s" in %s (you may run '
                         'with --multi)' % (jfilter.field, jfilter.part))
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
            if last_c not in '{[':
                text_nice += '\n' + ' ' * INDENT_STEP * indent_level
        text_nice += c

        if c == ':' and not in_string:
            text_nice += ' '
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


def jsort(text):
    "Return json text sorted"
    import json
    data = json.loads(text)
    return expand(sort(data))


def sort(x):
    "Return a string that represents object x as a sorted json"
    if type(x) == str:
        return jstr(x)
    elif type(x) == dict:
        return '{%s}' % ','.join('%s:%s' % (jstr(k), sort(x[k]))
                                  for k in sorted(x.keys()))
    elif type(x) == list:
        return '[%s]' % ','.join(sort(xi) for xi in sorted(x, key=sort_key))
    elif type(x) == bool:
        return 'true' if x else 'false'
    else:
        return str(x)


def jstr(x):
    "Return a json representation of the given string"
    return '"%s"' % x.replace('"', '\\"')


def sort_key(x):
    "Return a sorting key depending on the type of x"
    if type(x) == dict:
        if 'name' in x:
            return x['name']
        elif 'id' in x:
            return x['id']
        else:
            return 'A'
    elif type(x) == str:
        return x
    else:
        return 'A'



if __name__ == '__main__':
    main()
