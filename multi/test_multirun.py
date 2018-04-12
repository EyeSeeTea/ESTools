# Tests for multirun.py
#
# You can run them with pytest test_multirun.py

from tempfile import NamedTemporaryFile
from subprocess import check_output

import multirun

sample_commands = """
ls
    ls -l
# Next one is tricky
create_authorized_keys
    mkdir -m 700 /home/admin/.ssh
    chown admin.admin /home/admin/.ssh
    touch /home/admin/.ssh/authorized_keys
    chown admin.admin /home/admin/.ssh/authorized_keys
    chmod 600 /home/admin/.ssh/authorized_keys
install_zabbix_agent
    sudo apt-get install -y zabbix-agent
get_zabbix_id
    id zabbix
create_zabbix
    useradd --create-home --shell /bin/false zabbix
create_admin
    useradd --create-home --shell /bin/bash admin
    usermod --append --groups sudo admin
version
    cat /etc/debian_version
"""


def test_parse_commands():
    with NamedTemporaryFile('wt') as tmp:
        tmp.write(sample_commands)
        tmp.flush()
        commands = multirun.parse_commands(tmp.name)
        assert 'create_zabbix' in commands
        assert commands['get_zabbix_id'].strip() == 'id zabbix'


def test_get_command():
    with NamedTemporaryFile('wt') as tmp:
        tmp.write(sample_commands)
        tmp.flush()
        f = multirun.get_command('get_zabbix_id', tmp.name,
                                 literal=False)
        # If could do "ssh localhost" without being asked for a password,
        # then we could do the following check:
        #   assert f('localhost').strip() == check_output('id zabbix')


def test_associate():
    assert (multirun.associate(lambda x: x*x, range(10)) ==
            {x: x*x for x in range(10)})
