#!/bin/bash
#
# Replace user system with username superuser (password: 'district')
#

create_superuser() { local server_url=$1
  local user_id
  local filter="userCredentials.username:eq:system"
  local fields="id,userCredentials[username]"

	user_id=$(curl -sS -g "$server_url/api/users?fields=$fields&filter=$filter" | jq -r '.users[0] | .id')
  echo "System UID = $user_id"

	if test "$user_id" = "null"; then
		echo "Cannot find system user"
		exit 1
	else
	 	local json='{"username": "superuser", "password": "Super123"}'
		curl -sS -d "$json" "$server_url/api/users/$user_id/replica" -H "Content-Type:application/json"
    echo
    echo "User replicated from <system> created: superuser/Super123"
	fi
}

main() {
  if test "$#" -ne 1; then
    echo "Usage: $(basename "$0") SERVER_URL"
    exit 1
  else
  	local server_url=$1
  	create_superuser "$server_url"
  fi
}

main "$@"
