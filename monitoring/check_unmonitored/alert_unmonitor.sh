#!/bin/bash

# Just a simple wrapper around the check script.
# This is where the different custom settings for the alerting are configured: time, include regex, exclude regex, proxy

# ignore unmonitored services until MAXTIME seconds (to avoid alerting during some maintenance)
MAXTIME=3600

# scripts
DIRPATH=$(dirname "${0}")
CHECKER_SCRIPT=${DIRPATH}/check_unmonitor.sh
NOTIFIER_SCRIPT=${DIRPATH}/../../DHIS/webhook_notifier/webhook_notifier.py

WEBHOOK_URL=https://example.com/webhook/xxxxxxxxx

TITLE_UNMONITOR="Unmonitored services detected on ${HOSTNAME}"
TITLE_ERROR="There are some issues with the monit service on ${HOSTNAME}"

# request MD output
CHECKER_PARAMETERS="${CHECKER_PARAMETERS} -m"
# filter unmonitored services until they have been at least MAXTIME seconds unmonitored
CHECKER_PARAMETERS="${CHECKER_PARAMETERS} -t ${MAXTIME}"
# include services that matches this regex
#CHECKER_PARAMETERS="${CHECKER_PARAMETERS} -i <regex>"
# exclude services that matches this regex
#CHECKER_PARAMETERS="${CHECKER_PARAMETERS} -e <regex>"

# establish proxy settings
#NOTIFIER_PARAMETERS="${NOTIFIER_PARAMETERS} --http-proxy <proxy>"
#NOTIFIER_PARAMETERS="${NOTIFIER_PARAMETERS} --https-proxy <proxy>"
# add the rest of the fixed parameters to the notifier script
NOTIFIER_PARAMETERS="${NOTIFIER_PARAMETERS} --webhook-url ${WEBHOOK_URL}"

# Run checker script with established parameters
checker_output=$(${CHECKER_SCRIPT} ${CHECKER_PARAMETERS})
checker_rc=$?

# error during execution of the checker script
if [[ ${checker_rc} -eq 1 ]] ; then
	notifier_output=$( ${NOTIFIER_SCRIPT} \
		           ${NOTIFIER_PARAMETERS} \
			   --title "${TITLE_ERROR}" \
			   --content "${checker_output}" )
				   #
# some services are unmonitored
elif [[ ${checker_rc} -eq 2 ]] ; then
	notifier_output=$( ${NOTIFIER_SCRIPT} \
	                   ${NOTIFIER_PARAMETERS} \
			   --title "${TITLE_UNMONITOR}" \
			   --content "${checker_output}" )

# No alert needed, all services are being monitored
else
	exit 0
fi

# if there was some error in the notifier script, log time of day and error text
if [[ "${notifier_output}" =~ ERROR ]] ; then

	echo "$(date -Iminutes) - There were errors during the notification"
	echo "${notifier_output}"
fi

exit ${checker_rc}

