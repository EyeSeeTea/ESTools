#!/bin/bash
set -e -u -o pipefail

sql() {
  psql -v ON_ERROR_STOP=1 "$@"
}

main() { local db=$1 setup_file=$2
  local interpretation_id="BR11Oy1Q4yR"
  local comment_id="oRmqfmnCLsQ"
  local object="chart/R9A0rvAydpn"

  cat "$setup_file" | sql "$db"

  echo "DELETE FROM keyjsonvalue WHERE namespace = 'notifications';" | sql "$db"

  echo "update interpretation set interpretationtext = 'new text$(date +%s)' where uid = '$interpretation_id';" | sql "$db"
  curl -f -sS -u "admin:district"  -d "Int:$(date +%s)" -H 'Content-Type: text/plain' -X POST \
    "http://localhost:8080/api/29/interpretations/$object" | jq

  echo "update interpretationcomment set commenttext = 'new text$(date +%s)' where uid = '$comment_id';" | sql "$db"
  curl -f -sS -u "admin:district"  -d "Comment:$(date +%s)" -H 'Content-Type: text/plain' -X POST \
    "http://localhost:8080/api/29/interpretations/$interpretation_id/comments" | jq

  echo "select * from keyjsonvalue order by created desc limit 5;" | sql "$db"
}

main "demo230" "trigger.sql"
