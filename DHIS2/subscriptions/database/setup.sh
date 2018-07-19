#!/bin/bash
set -e -u -o pipefail

sql() {
  psql -v ON_ERROR_STOP=1 "$@"
}

main() { local apiurl=$1 auth=$2 db=$3 setup_file=$4
  local namespace="notifications"
  cat "$setup_file" | sql "$db"

  echo "Delete existing notifications in data store"
  curl -f -sS -u $auth -X DELETE "$apiurl/dataStore/$namespace" | jq || true
}

main "http://localhost:8080/api" "admin:district" "demo230" "$(dirname "$0")/triggers.sql"
