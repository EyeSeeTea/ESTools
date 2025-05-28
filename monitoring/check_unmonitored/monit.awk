function readabletime(seconds) {
	minutes=0
	hours=0
	days=0
	if (seconds > 60) {
		minutes=(seconds - (seconds%60))/60
		seconds=seconds%60
	}
	if (minutes > 60) {
		hours=(minutes - (minutes%60))/60
		minutes=minutes%60
	}
	if (hours > 24) {
		days=(hours - (hours%24))/24
		hours=hours%24
	}
	return (days?days"d ":"") (hours?hours"h ":"") (minutes?minutes"m ":"") (seconds?seconds"s ":"")
}

# retrieve current epoch to calculate downtime
BEGIN {
	epochnow=systime()
	total=0
}
# Every monitored service starts without any leading space. Retrieve name and set flag to 0
DEBUG && /^[^ ]/ { print "DEBUG:",$0}
/^[^ ]/ {
	servicename=substr($2,2,length($2)-2);
	flag=0
	include=match(servicename, INCLUDE)
	exclude=match(servicename, EXCLUDE)
}

# If monitoring status includes "Not" (as in "Not monitored"), activate flag to collect data
DEBUG && /monitoring status/ { print "DEBUG:",$0}
/monitoring status/ && /Not/ {
	flag=1
}

# data collected is the last time monit has been able to retrieve data from that service, store it
DEBUG && /data collected/ { print "DEBUG:",$0}
/data collected/ && flag {
	cmd="date -d \""$4 " " $5 " " $6 " " $7"\" \"+%s\"" 
	cmd | getline epochlast
	if (DEBUG) print "cmd: "cmd"; now: "epochnow"; last: "epochlast
	howlong=epochnow - epochlast
	lastdate=readabletime(howlong)
	if (DEBUG) print "read", howlong "s, which is:", lastdate
}

# If there is an empty line (after printing out any service info, there is always an empty line, even in the last service), and the flag was activated, print the relevant information if it passes the filters
DEBUG && /^$/ { print "DEBUG:", "Block end, flag:", flag, "include:", include, "exclude:", exclude, "howlong:", howlong}
/^$/ && flag && (include>0) && (exclude<1) && howlong >= MAXTIME {
	total=total+1
	if (FORMAT == 1) { # shortened format
		print servicename, howlong
	} else if (FORMAT == 2) { # markdown
		print "- **" servicename "** not monitorized for `" lastdate "`"
	} else { # default CLI output
		print "'" servicename "' not monitorized for " lastdate
	}
}

# Just return the number of processes that passed the filter
END {
	if (DEBUG) { print "DEBUG: END RC:", total}
	exit total
}
