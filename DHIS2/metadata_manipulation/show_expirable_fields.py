#!/usr/bin/env python3

"""
Find programrules, programrulevariables, dataelements and
trackedentityattributes. And then print them in order.

The idea is so we can compare them pre- and post-import.
"""

import sys
import re


regexps = [
    '<programRule [^/]+?>',
    '<programRuleVariable [^/]+?>',
    '<dataElement [^/]+?>',
    '<trackedEntityAttribute [^/]+?>',
]



def main():
    if len(sys.argv) < 2:
        sys.exit('usage: %s <xml_file>' % sys.argv[0])

    text = open(sys.argv[1]).read()
    text_new = ''
    for regexp in regexps:
        text_new += extract(text, regexp)

    print(add_newlines(text_new), end='')


def extract(text, regexp):
    "Return the parts of the text that match the given regexp, in order"
    # Also remove the "lastUpdated" and "created" parts.
    lines = []
    for match in re.finditer(regexp, text):
        txt = match.group()
        txt = remove(txt, 'lastUpdated=[^ ]+')
        txt = remove(txt, 'created=[^ ]+')
        lines.append(txt)
    return ''.join(sorted(lines))


def remove(text, regexp):
    "Return text without the regions matched by the expression regexp"
    text_new = ''
    last_end = 0
    for match in re.finditer(regexp, text):
        text_new += text[last_end:match.start()]
        last_end = match.end()
    text_new += text[last_end:]
    return text_new


def add_newlines(txt):
    txt_new = ''
    for c in txt:
        if c == '>':
            txt_new += c + '\n'
        else:
            txt_new += c
    return txt_new



if __name__ == '__main__':
    main()
