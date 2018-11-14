#!/usr/bin/env python3

"""
Run command on multiple nodes, in parallel.
"""

import subprocess as sp
from concurrent.futures import ThreadPoolExecutor as Pool, as_completed
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt


def main():
    try:
        args = get_arguments()
        nodes = get_nodes(args.hosts_file)
        multirun(args.command, nodes, args.timeout)
    except (AssertionError, OSError) as e:
        print(e)


def get_arguments():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('command', help='command to run')
    add('--hosts-file', default='multirun_hosts.txt',
        help='file with hosts to run command on')
    add('--timeout', type=int, default=10, help='number of seconds to wait')
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


def run(node, command, timeout):
    "Run command in given node and return its output"
    out = sp.check_output(['ssh', node, '/bin/sh'], stderr=sp.STDOUT,
                          timeout=timeout, input=command.encode('utf8'))
    return out.decode('utf8').strip()


def multirun(command, nodes, timeout=10, max_workers=10):
    "Run command in nodes and print its ouput, computed in parallel"
    f = lambda node: run(node, command, timeout)
    with Pool(max_workers) as pool:
        future_to_node = {pool.submit(f, x): x for x in nodes}
        for future in as_completed(future_to_node):
            node = future_to_node[future]
            try:
                out = future.result()
                print('%-20s %s' % (node, out))
            except Exception as e:
                print('%-20s %s' % (node, e))



if __name__ == '__main__':
    main()
