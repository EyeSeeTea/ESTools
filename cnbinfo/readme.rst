Description
Is a python script that get all the usernames and ids for a given users list.
First, we need to generate this user list file. You can generate it by running:
  ./multirun.py --literal 'cat /etc/passwd' > users.txt
And then you can run  ./extract_users.py without arguments.

Usage

Run, where multirun.py is located:

  ./multirun.py --literal 'cat /etc/passwd' > users.txt

And then run where extract_users is located:

  ./extract_users
You need user.txt is also located in the same directory. Copy or move it if necessary.

