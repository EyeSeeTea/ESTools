#!/usr/bin/env python3

"""
Remove users, userAccesses and userGroupAccesses from a metadata export.
"""

import sys
import re


regexps = [
    '<userGroupAccesses>.*?</userGroupAccesses>',
    '<userAccesses>.*?</userAccesses>',
    '<users>.*?</users>']
# Those are for xml. For json it would be:
#   r'"userGroupAccesses":\[\{.*?\}\],',
#   r',"userAccesses":\[\{.*?\}\]',
#   r',"user":\{.*?\}']



def main():
    if len(sys.argv) < 2:
        sys.exit('usage: %s <xml_file>' % sys.argv[0])

    text = open(sys.argv[1]).read()
    for regexp in regexps:
        text = remove(text, regexp)
    print(text, end='')


def remove(text, regexp):
    "Return text without the regions matched by the expression regexp"
    text_new = ''
    last_end = 0
    for match in re.finditer(regexp, text):
        text_new += text[last_end:match.start()]
        last_end = match.end()
    text_new += text[last_end:]
    return text_new



if __name__ == '__main__':
    main()
