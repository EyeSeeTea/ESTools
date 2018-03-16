#!/usr/bin/env python3

"""
Compare files between hosts (that we can directly access with ssh).
"""

import sys
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
            fetch(args.hosts[0], args.path, tmp0.name, args.sudo)
            fetch(args.hosts[1], args.path, tmp1.name, args.sudo)
            sp.call(args.cmpprog.split() + [tmp0.name, tmp1.name])


def parse_arguments():
    parser =  ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('path', default='/etc/debian_version',
        help='full path to the file we want to compare in the remote systems')
    add('--hosts', nargs=2, metavar='HOST', default=['arquimedes', 'behring'],
        help='remote hosts with the files we want to compare')
    add('--sudo', action='store_true', help='if need sudo to access the files')
    add('--cmpprog', default='meld', help='program used to compare the files')
    add('--keep', action='store_true', help='keep the temporary copied files')
    return parser.parse_args()


def fetch(host, remotename, localname, sudo=False):
    "scp host:remotename localname, only fancier"
    try:
        if host == 'localhost':
            sp.check_output((['sudo'] if sudo else []) +
                            ['cp', remotename, localname])
            return

        if not sudo:
            sp.check_output(['scp', '%s:%s' % (host, remotename), localname])
        else:
            command = ('sudo cat %s' % remotename).encode('utf8')
            out = sp.check_output(['ssh', host, '/bin/sh'], stderr=sp.STDOUT,
                                  input=command).decode('utf8')
            open(localname, 'wt').write(out)
    except sp.CalledProcessError as e:
        sys.exit('%s\nMaybe try with/without the "--sudo" argument?' % e)


def push(localname, host, remotename, sudo=False, backup=True):
    "scp localname host:remotename, only fancier"
    try:
        if not sudo:
            sp.check_output(['scp', localname, '%s:%s' % (host, remotename)])
        else:
            tempname = '_pushed_%s' % remotename.split('/')[-1]
            sp.check_output(['scp', localname, '%s:%s' % (host, tempname)])

            commands = ''
            if backup:
                commands += 'sudo cp %s %s.backup\n' % (remotename, remotename)
            commands += 'sudo mv %s %s' % (tempname, remotename)
            out = sp.check_output(['ssh', host, '/bin/sh'], stderr=sp.STDOUT,
                                  input=command, universal_newlines=True)
    except sp.CalledProcessError as e:
        sys.exit('%s\nMaybe try with/without the "--sudo" argument?' % e)



if __name__ == '__main__':
    main()
