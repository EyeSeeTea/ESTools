Utilities related to managing multiple hosts.

* `compare.py` - compare files existing in two remote hosts.
* `multirun.py` - run commands on multiple remote hosts.

multirun.py
===========

Run the same command in multiple hosts in parallel (by using
asynchronous calls) and show the results.

`multirun.py` reads the given command (normally given in between
quotes so the shell doesn't break it) on the hosts specified by
`multirun_hosts.txt` or whatever file is mentioned in the
`--hosts-file` argument.

You can choose between a short (everything in one line) and long
(output appears in several lines) version of the output. To do so, use
the `--format` argument.

Example
-------

To find out the kernel version on all the hosts that appear in
`multirun_hosts.txt`, you can simply run::

  $ ./multirun.py 'uname -a'

To list the files and directories in `/` and show them with newlines
included in between::

  $ ./multirun.py --format long 'ls /'

Usage
-----

usage:
  multirun.py [-h] [--hosts-file HOSTS_FILE] [--timeout TIMEOUT] [--format {short,long}] command

positional arguments:
  command               command to run

optional arguments:
  -h, --help                show this help message and exit
  --hosts-file HOSTS_FILE   file with hosts to run command on (default:  multirun_hosts.txt)
  --timeout TIMEOUT         number of seconds to wait (default: 10)
  --format short_long       output format (default: short)
