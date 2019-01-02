extract_users.py
================

Description
-----------

Is a python script that get all the usernames and ids for a given users list.
First, we need to generate this user list file. You can generate it by running:

$ ./multirun.py --literal 'cat /etc/passwd' > users.txt

And then you can run 

$ ./extract_users.py without arguments.


**Usage:**

First, run:

$ ./multirun.py --literal 'cat /etc/passwd' > users.txt

,multirun.py is located in ../multi path

user.text format looks like /etc/passwd format:

tom\:x :\1000:1000:Vivek  Gite:/home/vivek:/bin/bash
...

Where first one is the username. Second the password (an x character indicates that encrypted password is stored in /etc/shadow file). Next one is User ID (UID). Then, follows the Group ID (GID). Next (Vivek Gite) is a user ID Info: a comment field.
Finally we have the absolute path to the home directory and the absolute path of a command or shell (/bin/bash).

And then run extract_users.py:

$ ./extract_users.py

You need user.txt is also located in the same directory. Copy or move it if necessary.

The output looks like:

hostname,tom,1000
...

we have an alphabetical ordered list (by its hostname) with all the users in all the machines, one in each line, in this output format:

hostname,user,IUD
hostname,user,IUD
hostname,user,IUD



