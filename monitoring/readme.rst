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

It reads the datasets and the users to check from a configuration
file, that has an email associated to each space where it should send
alerts. The file `space_monitor.cfg` is included as an example.

If we want to check periodically every 5 minutes, we can add the
following line to the crontab::

  */5 * * * * /path/to/space_monitor.py --config /path/to/space_monitor.cfg >> /path/to/space_monitor.log 2>&1
