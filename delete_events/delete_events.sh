#!/bin/bash

#################
# EyeSeeTea Ltd #
#################

# INSTRUCTIONS: This script just concatenates http calls to the web API of a DHIS2 server to remove
#  a list of events from that server. Just configure the server URL in the server variable, a user with
#  permission to delete the events in the user variable, its password in the pass variable and please
#  introduce the list of event UUIDs in a file called events.list with each UUID in one separate line

# REQUIREMENTS: This script is written for bash shell, and needs curl to be installed in the system

# OUTPUT: The script will prompt the result of each call and there will be a delete_events.log file with
#  the concatenation of the json files returned by each call

server=https://hnqis-dev-ci.psi-mis.org
user=admin
pass=district
events=( $(cat events.list) )
LOG_FILE=delete_events.log

echo "----------" > ${LOG_FILE} 
echo "Execution started: $(date)" >> ${LOG_FILE}
echo "----------" >> ${LOG_FILE} 
for eventID in ${events[@]}; do
  echo "deleting ${eventID}"
  curl -X DELETE "${server}/api/events/${eventID}" -u ${user}:${pass} -v${event} >> ${LOG_FILE} 
  echo "" >> ${LOG_FILE}
done
echo "----------" >> ${LOG_FILE} 
echo "Execution finished: $(date)" >> ${LOG_FILE}
echo "----------" >> ${LOG_FILE} 

