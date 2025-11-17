#!/usr/bin/env bash

#example usage:
# log_job_status_notificator.sh failed /home/tomcatuser/logs/dhis2/dhis2.log

if [[ $# -ne 2 ]]; then
  echo "Required: $0 <failed|completed> <log_file>"
  exit 1
fi

STATE_PATH="/path/to/processcatalinacontrol"
# Required mkdirs -p STATE_PATH

# 1 parameter: mode (failed | completed). By default: failed
MODE="$1"

# 2º parameter: source log file.
LOG_FILE="$2"

case "$MODE" in
  failed)
    STATUS_WORD="failed"
    # State file: stores the last processed line number
    STATE_FILE="$STATE_PATH/dhis2_process_failed.state"
    ;;
  completed)
    STATUS_WORD="completed"
    # State file: stores the last processed line number
    STATE_FILE="$STATE_PATH/dhis2_process_completed.state"
    ;;
  *)
    echo "Error: invalid mode: '$MODE'"
    echo "Required: $0 <failed|completed> <log_file>"
    exit 1
    ;;
esac

SEARCH_PHRASE="Process ${STATUS_WORD} after"


########################################
# 1. Read last processed line from state
########################################
last_checked_line=0
if [[ -f "$STATE_FILE" ]]; then
  read -r last_checked_line < "$STATE_FILE"
  if ! [[ "$last_checked_line" =~ ^[0-9]+$ ]]; then
    last_checked_line=0
  fi
fi

########################################
# 2. Check log file
########################################
if [[ ! -f "$LOG_FILE" ]]; then
  echo "Log file not found: $LOG_FILE"
  exit 0
fi

# Current number of lines in the log
current_last_line=$(wc -l < "$LOG_FILE")

# If the log is empty, we just reset state and do nothing
if (( current_last_line == 0 )); then
  echo "Log file is empty (probably rotated). Resetting state."
  echo "0" > "$STATE_FILE"
  exit 0
fi

########################################
# 3. Detect rotation or truncation
#    (log has fewer lines than last time)
########################################
if (( current_last_line < last_checked_line )); then
  echo "Log file was rotated or truncated. Resetting state to current end."
  echo "0" > "$STATE_FILE"
  exit 0
fi


########################################
# 5. Read only the new lines and filter errors
########################################
#To avoid start in the already checked last line
start_line=$(( last_checked_line + 1 ))

new_errors=$(
  sed -n "${start_line},${current_last_line}p" "$LOG_FILE" | grep "$SEARCH_PHRASE" | grep 'TRACKER_IMPORT_JOB' | grep -v 'SYSTEM_VERSION_UPDATE_CHECK' | grep -v 'CONTINUOUS_ANALYTICS_TABLE' || true
)

# We have now checked up to the current end of file → update state
echo "$current_last_line" > "$STATE_FILE"

if [[ -z "$new_errors" ]]; then
  echo "No new '$SEARCH_PHRASE' lines."
  exit 0
fi

echo "'$SEARCH_PHRASE' lines found"
printf "%s\n" "$new_errors"

# Non-zero exit so Monit sends one alert with this batch
exit 1
