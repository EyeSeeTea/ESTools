#!/usr/bin/env python3

"""
Compare files between hosts (that we can directly access with ssh).
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
from tempfile import NamedTemporaryFile
import subprocess as sp


def main():
    args = parse_arguments()

    def named_temp(host):
        suffix = '_%s_%s.tmp' % (host, args.path.replace('/', '_'))
        return NamedTemporaryFile(dir='.', suffix=suffix, delete=not args.keep)

    with named_temp(args.hosts[0]) as tmp0:
        with named_temp(args.hosts[1]) as tmp1:
            fetch(args.hosts[0], args.path, tmp0.name)
            fetch(args.hosts[1], args.path, tmp1.name)
            sp.call(args.cmpprog.split() + [tmp0.name, tmp1.name])


def parse_arguments():
    parser =  ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('path', default='/etc/debian_version',
        help='full path to the file we want to compare in the remote systems')
    add('--hosts', nargs=2, metavar='HOST', default=['arquimedes', 'behring'],
        help='remote hosts with the files we want to compare')
    add('--cmpprog', default='meld', help='program used to compare the files')
    add('--keep', action='store_true', help='keep the temporary copied files')
    return parser.parse_args()


def fetch(host, remotename, localname):
    sp.call(['scp', '%s:%s' % (host, remotename), localname])



if __name__ == '__main__':
    main()