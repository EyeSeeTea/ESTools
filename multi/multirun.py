#!/usr/bin/env python3

"""
Run command on all the accessible nodes at CNB.
"""

import sys
import subprocess as sp
from concurrent.futures import ThreadPoolExecutor as Pool
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt


def main():
    args = parse_arguments()
    command = get_command(args.command, args.commands_file, args.literal)
    nodes = get_nodes(args.hosts_file)

    outputs = associate(command, nodes)

    for node in nodes:
        print('%-20s %s' % (node, outputs[node]))


def parse_arguments():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('command', help='command to run')
    add('--literal', action='store_true', help='run the command literally')
    add('--commands-file', default='multirun_commands.txt',
        help='file with available commands')
    add('--hosts-file', default='multirun_hosts.txt',
        help='file with hosts to run command on')
    return parser.parse_args()


def get_command(command, commands_file, literal):
    "Return function that runs a command in a given hostname"
    if literal:
        command_str = command
    else:
        available_commands = parse_commands(commands_file)
        if command not in available_commands:
            sys.exit('available commands (from %s):\n  %s' %
                     (commands_file, '|'.join(available_commands.keys())))
        command_str = available_commands[command]
    return lambda node: run(node, command_str)


def parse_commands(fname):
    "Return dict with command name and command string, parsed from fname"
    commands = {}
    current_command = None
    command_str = ''
    new_command = lambda txt: len(txt) > 1 and txt[0] not in [' ', '\t', '\n']

    for line in open(fname):
        if len(line.strip()) == 0 or line.lstrip().startswith('#'):
            continue
        if new_command(line):
            if current_command:
                commands[current_command] = command_str
            command_str = ''
            current_command = line.strip()
        else:
            command_str += line.lstrip()
    if current_command:
        commands[current_command] = command_str
    command_str = ''

    return commands


def get_nodes(fname):
    "Return list of nodes read from fname"
    nodes = []
    for line in open(fname):
        if len(line.strip()) == 0 or line.lstrip().startswith('#'):
            continue
        nodes.append(line.strip())
    return nodes


def run(node, command_str):
    "Run command in given node and return its output"
    try:
        out = sp.check_output(['ssh', node, '/bin/sh'], stderr=sp.STDOUT,
                              input=command_str.encode('utf8'))
        return out.decode('utf8').strip()
    except sp.CalledProcessError as e:
        return str(e)


def associate(f, a, max_workers=10):
    "Return {x: f(x) for x in a} computed in parallel"
    a = list(a)  # in case it was a set, to respect the order
    with Pool(max_workers) as pool:
        return dict(zip(a, pool.map(f, a)))



if __name__ == '__main__':
    main()
