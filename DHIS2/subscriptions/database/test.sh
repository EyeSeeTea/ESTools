#!/bin/bash
set -e -u -o pipefail

sql() {
  psql -v ON_ERROR_STOP=1 "$@"
}

main() { local apiurl=$1 auth=$2 db=$3 setup_file=$4
  local interpretation_id="BR11Oy1Q4yR"
  local comment_id="oRmqfmnCLsQ"
  local object1="chart/R9A0rvAydpn"
  local object2="reportTable/tWg9OiyV7mu"
  local object3="eventReport/YZzuVprU7aZ"
  local namespace="notifications"

  cat "$setup_file" | sql "$db"

  echo "Delete existing notifications in data store"
  curl -f -sS -u $auth -X DELETE "$apiurl/dataStore/$namespace" | jq || true
  
  echo "Create interpretation"
  curl -f -sS -u $auth -d "Int:$(date +%s)$RANDOM" -H 'Content-Type: text/plain' -X POST \
    "$apiurl/interpretations/$object1" | jq

  echo "Create interpretation 2"
  curl -f -sS -u $auth -d "Int:$(date +%s)$RANDOM" -H 'Content-Type: text/plain' -X POST \
    "$apiurl/interpretations/$object2" | jq

  echo "Create interpretation 3"
  curl -f -sS -u $auth -d "Int:$(date +%s)$RANDOM" -H 'Content-Type: text/plain' -X POST \
    "$apiurl/interpretations/$object3" | jq

  echo "Update interpretation: $interpretation_id"
  curl -f -sS -u $auth -d "Int:$(date +%s)$RANDOM" -H 'Content-Type: text/plain' -X PUT \
    "$apiurl/interpretations/$interpretation_id" | jq

  echo "Update comment: $comment_id"
  curl -f -sS -u $auth -d "Int:$(date +%s)-$RANDOM" -H 'Content-Type: text/plain' -X PUT \
    "$apiurl/interpretations/$interpretation_id/comments/$comment_id" | jq

  echo "Create comment"
  curl -f -sS -u $auth -d "Comment:$(date +%s)" -H 'Content-Type: text/plain' -X POST \
    "$apiurl/interpretations/$interpretation_id/comments" | jq

  echo "select * from keyjsonvalue WHERE namespace = 'notifications' order by created desc;" | sql "$db"
}

main "http://localhost:8080/api" "admin:district" "demo230" "$(dirname "$0")/triggers.sql"
