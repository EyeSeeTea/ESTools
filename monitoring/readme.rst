There are two monitors in this directory.

monitor.py
----------

Simple monitor that stays in memory and pings periodically a set of
computers.

To use it, you need to fill the following values in `monitor.py`::

  EMAIL_USER
  EMAIL_PASSWD
  webs
  processing
  storage
  backups
  dead
  disappeared

For more information, run `./monitor.py --help`.

To run the unit tests, use the following command in this directory::

  pytest-3


space_monitor.py
----------------

Monitors the space left in a ZFS system and alerts whenever more than
80% of the quota (or available space) is used.

Use with a configuration file (`space_monitor.cfg` is included as an
example).
