#!/usr/bin/env bash
set -euo pipefail


OUTDIR="/backup/logs/job_monitor"

ts_human="$(date +'%d-%m-%Y_%H-%M-%S')"
file="$OUTDIR/${ts_human}.csv"

#hardcoded secrets file with the $db_local source as export db_local=xxx
source secrets_file

QUERY=" FROM jobconfiguration
WHERE schedulingtype = 'ONCE_ASAP'
  AND jobstatus = 'SCHEDULED'
  AND lastexecutedstatus = 'NOT_STARTED'
  AND created < NOW() - interval '10 minutes'"
#Commented, used only to test the script
#QUERY=" FROM jobconfiguration WHERE jobstatus = 'SCHEDULED'"
 
rows=$(psql -X -At -v ON_ERROR_STOP=1 -d "$db_local" -c "SELECT COUNT(*) $QUERY;")

if (( rows == 0 )); then
#no errors
  exit 0
fi

psql -X -v ON_ERROR_STOP=1 -d "$db_local" -c "\copy ( SELECT * $QUERY ) TO '$file' WITH CSV HEADER"

echo "Detailed info: ${ts_human}.csv"
exit 1
