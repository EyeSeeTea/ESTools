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

        display = get_display(nodes, args.short, args.literal)

        for node, out in multirun(args.command, nodes, args.timeout):
            print(display(node, out))

    except (AssertionError, OSError) as e:
        sys.exit(e)


def get_arguments():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)

    add = parser.add_argument  # shortcut
    add('command', help='command to run')
    add('-f', '--hosts-file', default='hosts.txt', help='file with hosts')
    add('-t', '--timeout', type=int, default=10, help='seconds to wait')
    add('-s', '--short', action='store_true', help='short output format')
    add('-l', '--literal', action='store_true', help='do not parse response')

    return parser.parse_args()


def get_nodes(fname):
    "Return list of nodes read from fname"
    nodes = []

    for line in open(fname):
        if len(line.strip()) == 0 or line.lstrip().startswith('#'):
            continue  # so there can be comments and empty lines too

        parts = line.strip().split()

        assert len(parts) == 1 or parts[1].startswith('#'), \
            'Malformed line in %s: %r' % (fname, line)

        nodes.append(parts[0])

    return nodes


def get_display(nodes, short, literal):
    "Return a function that, given a node and its output, formats it prettily"
    if short:
        fmt = '%%-%ds # %%s' % max(len(x) for x in nodes)
        if literal:
            return lambda node, out: fmt % (node, out)
        else:
            return lambda node, out: fmt % (node, out.replace('\n', ' '))
    else:
        return lambda node, out: f'==> {node} <==\n{out}\n'


def multirun(command, nodes, timeout=10, max_workers=10):
    "Run command in nodes and yield their output, computed in parallel"
    def run(node):
        proc = sp.run(['ssh', node, '/bin/sh'], input=command.encode('utf8'),
                      capture_output=True, timeout=timeout)
        stderr = proc.stderr.decode('utf8').strip()
        stdout = proc.stdout.decode('utf8').strip()
        return (('' if proc.returncode == 0 else f'=> [{proc.returncode}]\n') +
                ('' if not stderr else f'=> stderr:\n{stderr}\n=> stdout:\n') +
                stdout)

    with ThreadPoolExecutor(max_workers) as executor:
        future_to_node = {executor.submit(run, node): node for node in nodes}
        for future in as_completed(future_to_node):
            node = future_to_node[future]
            yield node, future.result()



if __name__ == '__main__':
    main()
