#!/usr/bin/env python3

"""
Run command on all the accessible nodes at CNB.
"""

import sys
import subprocess as sp
from concurrent.futures import ThreadPoolExecutor as Pool

nodes_all = set("""\
arquimedes behring
cnb-asimov cnb-asimov-dos cnb-campins cnb-carver cnb-clark-cinco cnb-clark6
cnb-copernico cnb-disco-tres cnb-einstein cnb-einstein-dos cnb-euler
cnb-faraday cnb-galois cnb-hilbert cnb-lagrange cnb-nolan cnb-peano
cnb-heisenberg cnb-rinchen cnb-rinchen-dos cnb-scipionbox i2pc
""".split())

nodes_with_admin = set("""\
arquimedes behring
cnb-asimov cnb-asimov-dos cnb-campins cnb-carver cnb-clark-cinco cnb-clark6
cnb-copernico cnb-euler cnb-faraday cnb-galois cnb-hilbert cnb-lagrange
cnb-nolan cnb-peano cnb-heisenberg cnb-rinchen cnb-rinchen-dos i2pc
""".split())

nodes_unreachable = set("""\
cnb-einstein cnb-einstein-dos cnb-disco-tres
""".split())

nodes_noroot = {'cnb-scipionbox'}

# heisenberg and pitagoras are the same


available_commands = {
    'get_zabbix_id': 'id zabbix',
    'create_zabbix': 'useradd --create-home --shell /bin/false zabbix',
    'create_admin': """
        useradd --create-home --shell /bin/bash admin
        usermod --append --groups sudo admin""",
    'find_guybrush': 'grep -o guybrush .ssh/authorized_keys',
    'version': 'cat /etc/debian_version',
    'create_authorized_keys': """
        mkdir -m 700 /home/admin/.ssh
        chown admin.admin /home/admin/.ssh
        touch /home/admin/.ssh/authorized_keys
        chown admin.admin /home/admin/.ssh/authorized_keys
        chmod 600 /home/admin/.ssh/authorized_keys""",
}



def main():
    command = get_command()
    nodes = nodes_all - nodes_unreachable - nodes_noroot
    for node, out in associate(command, nodes).items():
        print('%-20s %s' % (node, out))


def get_command():
    "Return function that runs a command in a given hostname"
    if len(sys.argv) < 2 or sys.argv[1] not in available_commands:
        sys.exit('usage: %s <%s>' % (sys.argv[0],
                                     '|'.join(available_commands.keys())))
    command_str = available_commands[sys.argv[1]]
    return lambda node: run(node, command_str)


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
