#!/bin/bash
set -e -u -o pipefail
#
# Replicate user system with username superadmin

create_superadmin() { local server_url=$1
  local user_id
  local filter="userCredentials.username:eq:system"
  local fields="id,userCredentials[username]"

  user_id=$(curl -f -sS -g "$server_url/api/users?fields=$fields&filter=$filter" | jq -r '.users[0] | .id')
  echo "System UID = $user_id"

  if test "$user_id" = "null"; then
    echo "Cannot find system user"
    exit 1
  else
     local json='{"username": "superadmin", "password": "Super123"}'
    curl -sS -f -d "$json" "$server_url/api/users/$user_id/replica" -H "Content-Type:application/json"
    echo
    echo "User replicated from <system> created: superadmin/Super123"
  fi
}

main() {
  if test "$#" -ne 1; then
    echo "Usage: $(basename "$0") SERVER_URL"
    exit 1
  else
    local server_url=$1
    create_superadmin "$server_url"
  fi
}

main "$@"
