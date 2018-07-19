#!/bin/bash
set -e -u -o pipefail

sql() {
  psql -v ON_ERROR_STOP=1 "$@"
}

main() { local apiurl=$1 auth=$2 db=$3 setup_file=$4
  local object1="chart/R9A0rvAydpn"
  local object2="reportTable/tWg9OiyV7mu"
  local object3="eventReport/YZzuVprU7aZ"
  local namespace="notifications"
  local interpretation_id comment_id

  cat "$setup_file" | sql "$db"

  echo "Delete existing notifications in data store"
  curl -f -sS -u $auth -X DELETE "$apiurl/dataStore/$namespace" | jq || true

  # Interpretations
  
  echo "Create interpretation"
  interpretation_id=$(curl -f -sS -u $auth -d "Int:$(date +%s)$RANDOM" -H 'Content-Type: text/plain' -X POST \
    "$apiurl/interpretations/$object1" -i | grep "^Location" | awk -F'/' '{print $NF}' | sed "s/[[:space:]]*$//")

  echo "Create interpretation 2"
  curl -f -sS -u $auth -d "Int:$(date +%s)$RANDOM" -H 'Content-Type: text/plain' -X POST \
    "$apiurl/interpretations/$object2" | jq

  echo "Create interpretation 3"
  curl -f -sS -u $auth -d "Int:$(date +%s)$RANDOM" -H 'Content-Type: text/plain' -X POST \
    "$apiurl/interpretations/$object3" | jq

  echo "Update interpretation: $interpretation_id"
  curl -f -sS -u $auth -d "Int:$(date +%s)$RANDOM" -H 'Content-Type: text/plain' -X PUT \
    "$apiurl/interpretations/$interpretation_id" | jq

  # Comments

  echo "Create comment"
  comment_id=$(curl -f -sS -u $auth -d "Comment:$(date +%s)" -H 'Content-Type: text/plain' -X POST \
    "$apiurl/interpretations/$interpretation_id/comments" -i | grep "^Location" | awk -F'/' '{print $NF}' | sed "s/[[:space:]]*$//")

  echo "Update comment: $comment_id"
  curl -f -sS -u $auth -d "Int:$(date +%s)-$RANDOM" -H 'Content-Type: text/plain' -X PUT \
    "$apiurl/interpretations/$interpretation_id/comments/$comment_id" | jq

  curl -f -sS -u $auth "$apiurl/dataStore/notifications/ev-month-$(date +%Y-%m)" | jq
}

main "http://localhost:8080/api" "admin:district" "demo230" "$(dirname "$0")/triggers.sql"
