use-report
==========

* use-report is a bash script that estimates the size of each directories of /home 
  
This script is in asimov-dos machine in the path /etc/sysman/san/reports/simple/asimov2
(There is another one similar to these in asimov machine, in the path /etc/sysman/san/reports/simple/asimov, that works similarly to this one).

Usage
=====

It estimates the size of subfolders of /home in integer numbers of Gb, rounding up.

You can run the script ./use-report (ensure you have a log folder in the same path)
But a cron process runs it every wednesday al 6 am.
It works as follows:

1. The output is written in /tmp
--------------------------------

Example

For instance:
sudo du -hs /home/*
36K	/home/admin
1.1T	/home/coss
904M	/home/curso01
1.1G	/home/curso02
2.0G	/home/curso03
1.3G	/home/curso04
8.0K	/home/curso05
6.4T	/home/EMPIAR

sudo cat /tmp/tmp.QFHctJGqj5
# HOME
admin	1
coss	1095
curso01	1
curso02	2
curso03	2
curso04	2
curso05	1
EMPIAR	6475


2. Rewrite the output in /log folder
------------------------------------

The output written in /tmp is writen in /log folder (in the same path where is located the script) , but some unnecesary lines, such as:
# HOME 
lost+found 
are deleted.

Other lines, such as:
/home/aquota.group
/home/aquota.user 
are data file and they don't exist in asimov-dos /home, but they exist in asimov /home. They are rewriten.


3. Summarize all data
--------------------- 

Finally, it would integrate all the data into /var/log/disk_stats.log
In first column: seconds since 1970-01-01 00:00:00 UTC
Second column: date
Third column: time
Fourth column: hostname (asimov-dos, for instance)
Fifth column: Size of /home directories in Gb
And at the end, summarizes total, used and free size. 

An output of disk_stats.log is:
(...)
1547619500 20190116 071820 asimov-dos admin 1
1547619500 20190116 071820 asimov-dos coss 1095
1547619500 20190116 071820 asimov-dos curso01 1
1547619500 20190116 071820 asimov-dos curso02 2
1547619500 20190116 071820 asimov-dos curso03 2
1547619500 20190116 071820 asimov-dos curso04 2
1547619500 20190116 071820 asimov-dos curso05 1
1547619500 20190116 071820 asimov-dos EMPIAR 6475
1547619500 20190116 071820 asimov-dos joton 5036
1547619500 20190116 071820 asimov-dos jsegura 4769
1547619500 20190116 071820 asimov-dos ldelcano 898
1547619500 20190116 071820 asimov-dos marta 10
1547619500 20190116 071820 asimov-dos polito 8
1547619500 20190116 071820 asimov-dos rkoning 727
1547619500 20190116 071820 asimov-dos rmelero 4797
1547619500 20190116 071820 asimov-dos roberto 505
1547619500 20190116 071820 asimov-dos scipion 7
1547619500 20190116 071820 asimov-dos zabbix 1
1547619500 20190116 071820 asimov-dos TOTAL 34.9473 23.7657 11.1816

Where we can check each folder size, and we have 11 Gb free yet.
