use-report
==========

use-report is a bash script that estimates the size (as GB round up to integer numbers) of each directories at /home 
  
This script can be found in the following machines-paths:

   - asimov-dos -> /etc/sysman/san/reports/simple/asimov2 (cronjob at 6 am every Wednesday)
   - asimov -> /etc/sysman/san/reports/simple/asimov (cronjob at 6 am every Wednesday)

Differences between script in asimov (use-report-asimov) and asimov-dos (use-report-asimov2) are few and mostly related to different paths used for each machine. 

Note:
These scripts exists in clark-cinco, einstein-dos, nolan and rinchen but they do not work.
And there scripts which don't estimate the size of each directories of /home, but the used, total and free space in /nas/archive, /nas/backup, /nas/replicas and /nas/workand working fine in: faraday, nolan, peano and rinchen. (Cron job already at 6 am every Wednesday)


Usage
=====

You can run the script by executing ./use-report (ensure you have a log folder in the same path)

It works as follows:

1. The output is written in /tmp
--------------------------------

Example

For instance::

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

The output written at /tmp is copied to /log folder (in the same path where the script is located), however some unnecesary lines are removed, for instance::

   # HOME 
   lost+found 
   are deleted.

Other lines, such as::

   /home/aquota.group
   /home/aquota.user 

are data file and they don't exist in asimov-dos /home, but they exist in asimov /home. They are rewriten.


3. Summarize all data
--------------------- 

Finally, use-report integrates all the data into /var/log/disk_stats.log

An output of disk_stats.log is::

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

where each parameter from left to right are:

   - seconds since 1970-01-01 00:00:00 UTC
   - date
   - time
   - hostname
   - Size of /home directories in Gb

and at the end, it summarizes total, used and free size. 

and we have 11 Gb free yet.
