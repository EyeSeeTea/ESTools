extract_users.py
================

Description
-----------

Get all the usernames and ids for a given users list.

extract_users.py gets for each machine the username and id of each user. Output is given as a list (CSV) ordered alphabetically by the machine name (hostname) where each line has the following format: hostname,user,userid

First, we need to generate this user list file. You can generate it by running::

  $ ./multirun.py --literal 'cat /etc/passwd' > users.txt

And then you can run::

  $ ./extract_users.py (no arguments)


**Usage:**

To get the list of users, you can simply run::

  $ ./multirun.py --literal 'cat /etc/passwd' > users.txt

multirun.py is located at https://github.com/EyeSeeTea/ESTools/tree/master/multi. user.text format should look like /etc/passwd format:

.. code-block::
  tom\:x :\1000:1000:Vivek  Gite:/home/vivek:/bin/bash
  ...

where each parameter from left to right are:
   - username
   - password (an x character indicates that encrypted password is stored in /etc/shadow file)
   - user id (UID)
   - group id (GID)
   - user id Info
   - absolute path to the home directory
   - shell path

Copy the user.txt into the same directory as extract_user.py and run extract_users.py:

  $ ./extract_users.py

The output should look like:
.. code-block::
  hostname,tom,1000
  ...