#!/bin/bash

# default values, can be overriden by parameters
VERBOSE=0
DEBUG=0
# regex filters: Include anything; exclude empty strings
INCLUDE='.*'
EXCLUDE='^$'
# This allows to ignore unmonitored services that might have gone down recently
MAXTIME=60
# FORMAT = 0 - default format, CLI
# FORMAT = 1 - short format, only service name and seconds. Some output omitted.
# FORMAT = 2 - mark down format, mainly for notifications
FORMAT=0

# constants
# only filename, PATH is the same as this script
AWKFILE=monit.awk

while getopts "vqdmi:e:t:" opt; do
    case $opt in
        v)
            VERBOSE=1
            ;;
        m)
            FORMAT=2
            ;;
        q)
            FORMAT=1
            ;;
        d)
            DEBUG=1
            ;;
        i)
            INCLUDE="${OPTARG}"
            ;;
        e)
            EXCLUDE="${OPTARG}"
            ;;
        t)
            readtime="${OPTARG}"
            if [[ "${readtime}" =~ ^[0-9]+$ ]] ; then
                MAXTIME=${readtime}
            else
                echo "Invalid parameter, must be an integer"
                exit 1
            fi
            ;;
        *)
            echo "Usage: $0 [-v] [-q] [-d] [-e <regex>] [-i <regex>]"
            echo "    -v         Verbose"
            echo "    -q         Quiet - output abreviated, takes preference over other formatting"
            echo "    -m         MD - output in markdown"
            echo "    -d         Debug"
            echo "    -i regex   Include only services that matches \"regex\""
            echo "    -e regex   Exclude all services that matches \"regex\". This takes precedence over -i"
            echo "    -t time    Time in seconds to wait before sending an alert, default to ${MAXTIME} seconds"
            echo ""
            echo "RC:"
            echo "    0    OK - monit is running and all services are monitored"
            echo "    1    Error in monit command or input parameters"
            echo "    2    There are unmonitored services"
            echo ""
            echo "regex:"
            echo "    Note that you must single quote to avoid the expression to be expanded before it reaches the program"
            echo "    You must use doble escape sequences instead of a single one. I.E. \\\\* to match a single *"
            exit 0
            ;;
    esac
done

shift $((OPTIND - 1))

if [[ ${FORMAT} -gt 0 ]] ; then
    # override to avoid debugging info if not in CLI format
    VERBOSE=0
fi

if [[ $(id -u) -ne 0 ]] ; then 
    echo "monit requires to be run with privileges"
    exit 1
fi

DIRPATH=$(dirname "${0}")

tempfile=$(mktemp)
trap "rm -f ${tempfile}" EXIT INT TERM KILL ABRT HUP QUIT

# check if monit report any unmonitored service (to avoid parsing all status output every time)
unmonitored=$( monit report unmonitored -B 2>${tempfile} )
rc=$?

# retrieve command return code in case it fails to execute, print error log as is
if [[ ${rc} -ne 0 ]] ; then
    [[ ${FORMAT} -ne 1 ]] && echo "Error checking monit status"
    [[ ${VERBOSE} -gt 0 ]] && cat ${tempfile}
    exit 1
fi

if [[ ${unmonitored} -eq 0 ]] ; then
    [[ ${VERBOSE} -gt 0 ]] && echo "No unmonitored services were found"
    [[ ${DEBUG} -gt 0 ]] && monit report 2>&1
    exit 0
fi

# parse monit status output
# store output to put it at the end
# store RC of AWK which is the number of services that passed the filter checks
awkOUT=$( monit status -B \
	| awk -v INCLUDE="${INCLUDE}" \
	      -v EXCLUDE="${EXCLUDE}" \
	      -v FORMAT=${FORMAT} \
	      -v DEBUG=${DEBUG} \
	      -v MAXTIME=${MAXTIME} \
	      -f ${DIRPATH}/${AWKFILE} )
awkRC=$?

# nothing was filtered out
if [[ ${awkRC} -eq ${unmonitored} ]] ; then
    if [[ ${VERBOSE} -gt 0 ]] ; then
        if [[ ${unmonitored} -gt 1 ]] ; then
            echo "There are ${unmonitored} unmonitored services:"
        else
            echo "There is ${unmonitored} unmonitored service:" 
        fi
    fi

# some services were filtered ( awkRC != unmonitored )
else
    # not all were filtered
    if [[ ${awkRC} -gt 0 ]] ; then
        if [[ ${VERBOSE} -gt 0 ]] ; then
            echo "There are ${unmonitored} unmonitored services, ${awkRC} not filtered:" 
        fi

    # all were filtered ==> no (relevant) services unmonitored ( awkRC == 0 )
    else
        if [[ ${VERBOSE} -gt 0 ]] ; then
            if [[ ${unmonitored} -gt 1 ]] ; then
                echo "There are ${unmonitored} unmonitored services, but filtered" 
            else
                echo "There is ${unmonitored} unmonitored service, but filtered" 
            fi
        fi
	# force RC to 0 as no (revelant) services are unmonitored
        overrideRC=0
    fi
fi

# if NOT empty, retrieve output at the end of the program
[[ ! -z ${awkOUT} ]] && echo "${awkOUT}"

# defaults to RC=2 to signal some unmonitored service(s), can be changed if forced earlier
exit ${overrideRC:-2}
