#!/usr/bin/env python3

"""
Like cat on steroids to manipulate json files.

Its main utility is to read json data like the one produced by the
metadata export app in dhis2, and filter the different parts.

It can read json from a file (even if it's a zip file) or from stdin,
select a subset of sections, make string replacements, filter the
different parts (letting only elements in them whose selected field
matches the given regular expression), sort and compact the output.

A simple filter would look like:
  userGroups:name:HEP
which would select from the "userGroups" section only the elements that
have the letters "HEP" in some subfield called "name".

Instead of "HEP" one can use any regular expression, for example "^HEP"
if we want the name to start with "HEP", or "\.(dataentry|validator)$"
if we want it to end exactly with ".dataentry" or ".validator".

If instead of filtering sections we want to filter elements from
subsections, the filter will have as many ":" at the beginning as the
depth of the subsection. For example, to filter userGroupAccesses
(which may be inside a userGroup) and select only those with a
displayName that starts with HEP, the filter would look like:
  ::userGroupAccesses:displayName:^HEP

The filters can be either given with the --filters argument or read
from a file that contains one filter per line, with the --filters-file
argument.

It can be handy to manipulate metadata exported from dhis2, so it can
be imported in another instance.
"""
import sys
import re
from collections import namedtuple
from argparse import ArgumentParser, RawDescriptionHelpFormatter as fmt
import zipfile
import json

Filter = namedtuple('Filter', ['nesting', 'part', 'field', 'regexp'])

INDENT_STEP = 2

sort_fields = []


def main():
    args = get_args()

    text = get_text_from_input(args)

    text = expand(compact(text))  # normalize spacing

    text = apply_replacements(text, args.replacements)

    if args.include or args.exclude:
        text = select(text, args.include, args.exclude)

    filters = get_filters(args.filters, args.filters_file)
    text = apply_filters(text, filters, args.multi)

    if args.remove:
        for field in args.remove:
            text = remove_field(text, field)

    if args.sort:
        text = jsort(text)

    if args.compact:
        text = compact(text)

    text = fix(text)

    if args.stats:
        print_stats(text)
    else:
        write(args.output, text)


def get_args():
    "Parse command-line arguments and return them"
    global sort_fields

    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('input', nargs='*', help='input single or multiple files')

    add('-o', '--output', help='output file (write to stdout if not given')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--filters', nargs='+', metavar='FILTER',
                       help='part:field:regexp selection filters')
    group.add_argument('--filters-file', help='file with selection patterns')
    add('-m', '--multi', action='store_true',
        help='allow multiple matches for field (uses the last match)')
    add('--include', nargs='+', metavar='SECTION', help='sections to include')
    add('--exclude', nargs='+', metavar='SECTION', help='sections to exclude')
    add('--remove', nargs='+', metavar='FIELD', help='sections to remove')
    add('--replacements', nargs='+', metavar='FROM TO', default=[],
        help='text to replace')
    add('-s', '--sort', action='store_true', help='output a sorted json')
    add('--sort-fields', nargs='+', metavar='FIELD',
        default=['name', 'id', 'property'],
        help='fields to use for sorting the elements')
    add('-c', '--compact', action='store_true', help='output a compacted json')
    add('-t', '--stats', action='store_true', help='print stats about json file instead of the file')
    args = parser.parse_args()

    sort_fields = args.sort_fields

    validate_input_file(args.input)

    if file_arg_maybe_misplaced(args.input, args.filters):
        print('Warning: no file given, but one of the filters looks '
              'like a filename.')

    return args


def validate_input_file(input):
    if input is None:
        print('Error: a input file must be provided. Read jcat -h for more info.')
        exit(0)


def file_arg_maybe_misplaced(fname, filters):
    return not fname and filters and not all(':' in x for x in filters)


def get_text_from_input(args):
    if len(args.input) > 0:
        text = read_multiple_files(args.input)
    else:
        text = read(args.input)
    return text


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
    for line_dirty in open(fname, encoding="utf-8"):
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
        with zf.open(zf.filelist[0], encoding="utf-8") as fin:
            return fin.read().decode('utf8')
    else:
        with open(fname, encoding="utf-8") as fin:
            return fin.read()


def read_multiple_files(input):
    "Return a text with all the input files merged"
    text = None

    for fname in input:
        fname = read(fname)
        if text is None:
            text = fname
            continue
        text = join(text, fname)

    return text


def join(text, fname):
    "Return text with all the file root elements added"
    text = json.loads(text)
    fname = json.loads(fname)
    for key, value in fname.items():
        if key in text:
            if isinstance(text[key], dict):
                text[key] = [text[key], value]
            else:
                text[key] += value
        elif isinstance(value, list):
            text[key] = value
        else:
            text.update(value)
    return json.dumps(text, ensure_ascii=False)

def print_stats(text):
    "Prints the object keys and number of objects inside each collection at root level"
    stats = json.loads(text)
    for key, value in stats.items():
        print("%s : %d objects" % (key, len(value)))

def write(fname, text):
    if fname:
        with open(fname, 'wt', encoding="utf-8") as fout:
            fout.write(text)
    else:
        print(text, end='')


def select(text, include, exclude):
    "Return a json text with only the selected sections"
    text_selected = '{\n'
    current_section = ''
    for line in text.splitlines():
        if not line.startswith(' '):
            continue  # avoid initial and final {}

        if line.startswith(' ' * INDENT_STEP + '"'):
            current_section = line.split('"', 2)[1]

        if ((include and current_section in include) or
            (not include and current_section not in exclude)):
            text_selected += line + '\n'

    text_selected += '}\n'

    if text_selected.endswith(',\n}\n'):
        text_selected = text_selected[:-4] + '\n}\n'

    return text_selected


def apply_filters(text, filters, multi):
    for jfilter in filters:
        text = filter_parts(text, jfilter, multi)
    return text


def remove_field(text, field):
    "Removed all the appearances of the given field in text"
    text_filtered = ''
    in_field = False
    for line in text.splitlines():
        line_stripped = line.lstrip()
        if not in_field:
            if line_stripped.startswith('"%s":' % field):
                indent = len(line) - len(line.lstrip())
                in_field = True
            else:
                text_filtered += line + '\n'
        else:
            if len(line) - len(line_stripped) <= indent:
                in_field = False
                if (len(line) - len(line_stripped) < indent or
                    line_stripped[0] not in ['}', ']']):
                    text_filtered += line + '\n'
    return text_filtered


def filter_parts(text, jfilter, multi=False):
    "Return a json text with only the elements that pass the jfilter filter"
    # That is, that match the regexp for the given field in the given part.
    # The text must be an expanded json.
    text_filtered = ''
    indent = 0  # indentation level of the part we will filter
    in_part = False  # are we in the part we want to filter?
    current_region = ''  # region we are scanning and may not include
    current_field = ''  # field that is being defined (like "name":...)
    for line in text.splitlines():
        if not in_part:
            spaces = ' ' * INDENT_STEP * jfilter.nesting
            if line.startswith('%s"%s":' % (spaces, jfilter.part)):  # start
                in_part = True
                indent = len(line) - len(line.lstrip())
            text_filtered += line + '\n'
        elif len(line) - len(line.lstrip()) <= indent:  # end part
            text_filtered += line + '\n'
            in_part = False
        elif line.startswith(' ' * (indent + INDENT_STEP) + '}'):  # end region
            current_region += line + '\n'
            if re.search(jfilter.regexp, current_field):
                text_filtered += current_region
            current_region = ''
            current_field = ''
        elif line.lstrip().startswith('"%s":' % jfilter.field):  # find field
            current_region += line + '\n'
            if not multi and current_field != '':
                sys.exit('Error: multiple fields named "%s" in %s (you may run '
                         'with --multi)' % (jfilter.field, jfilter.part))
            current_field = line.split('"')[3]  #   "field_name":"field_value"
        else:  # keep adding to region
            current_region += line + '\n'
    return text_filtered


def fix(text):
    "Return text without the trailing commas before end of lists/dicts"
    return re.sub(',(\s*(]|}))', r'\1', text)


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
    return '"%s"' % x.replace('\\"', '"').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')\
        .replace('\t', '\\t').replace("''", "\'\'")


def sort_key(x):
    "Return a sorting key depending on the type of x"
    global sort_fields
    if type(x) == dict:
        for field in sort_fields:
            if field in x and type(x[field]) == str:
                return x[field]
        else:
            return str(len(x))
    elif type(x) == str:
        return x
    elif type(x) == list:
        return str(len(x))
    else:
        return 'A'



if __name__ == '__main__':
    main()
