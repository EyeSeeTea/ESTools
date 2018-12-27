#!/usr/bin/env python3

"""
Run command on multiple nodes, in parallel.
"""

import sys
import subprocess as sp
from concurrent.futures import ThreadPoolExecutor, as_completed
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt


def main():
    try:
        args = get_arguments()
        nodes = get_nodes(args.hosts_file)
        display = get_display(args.format, nodes, args.literal)
        for node, out in multirun(args.command, nodes, args.timeout):
            display(node, out)
    except (AssertionError, OSError) as e:
        sys.exit(e)


def get_arguments():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('command', help='command to run')
    add('--hosts-file', default='multirun_hosts.txt',
        help='file with hosts to run command on')
    add('--timeout', type=int, default=10, help='number of seconds to wait')
    add('--format', default='short', choices=['short', 'long'],
        help='output format')
    add('--literal', action='store_true', help='do not parse the response')
    return parser.parse_args()


def get_nodes(fname):
    "Return list of nodes read from fname"
    nodes = []
    for line in open(fname):
        if len(line.strip()) == 0 or line.lstrip().startswith('#'):
            continue
        parts = line.strip().split()
        assert len(parts) == 1 or parts[1].startswith('#'), \
            'Malformed line in %s: %r' % (fname, line)
        nodes.append(parts[0])
    return nodes


def get_display(format_type, nodes, literal):
    "Return a function that, given a node and its output, displays it prettily"
    if format_type == 'short':
        fmt = '%%-%ds # %%s' % max(len(x) for x in nodes)
        return lambda node, out: print(fmt % (node, out if literal else out.replace('\n', ' ')))
    else:
        return lambda node, out: print('%s\n%s\n%s\n' %
                                       (node, '=' * len(node), out))


def multirun(command, nodes, timeout=10, max_workers=10):
    "Run command in nodes and yield their output, computed in parallel"
    def run(node):
        out = sp.check_output(['ssh', node, '/bin/sh'], stderr=sp.STDOUT,
                              input=command.encode('utf8'), timeout=timeout)
        return out.decode('utf8').strip()

    with ThreadPoolExecutor(max_workers) as executor:
        future_to_node = {executor.submit(run, node): node for node in nodes}
        for future in as_completed(future_to_node):
            node = future_to_node[future]
            try:
                yield node, future.result()
            except Exception as e:
                yield node, str(e)



if __name__ == '__main__':
    main()
