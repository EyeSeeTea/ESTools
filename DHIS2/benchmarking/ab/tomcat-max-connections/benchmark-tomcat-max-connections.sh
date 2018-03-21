#!/bin/bash
# Create table values tomcat maxConnection | XmxMemory | time elapsed
#
# Example, test with maxConnection=5,10,20; Xmx=2048,4096 on dev.eyeseetea.com:
#
#   bash benchmark-tomcat-max-connections.sh \
#     http://dev.eyeseetea.com:8081/dhis |
#     dev.eyeseetea.com:/data/dhis2/2.28/tomcat |
#     "5 10 20" |
#     "2048 4096" |
#     file-with-one-url-per-line.txt
set -e -u -o pipefail
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

debug() {
  echo "$@" >&2;
}

get_timestamp_ms() {
  echo $(($(date +%s%N)/1000000))
}

get_elapsed() {
  local ts_start=$(get_timestamp_ms)
  "$@"
  local ts_end=$(get_timestamp_ms)
  echo $((ts_end - ts_start))
}

ab_for_urls() { local concurrent_requests=$1; shift 1; local urls=$@
  local total_requests=$((2 * $concurrent_requests))

  for url in $urls; do
    debug "ab: $url"
    ab -q -A "admin:district" -n $total_requests -c $concurrent_requests -m GET -s 1000 "$url" >&2
  done
}

benchmark_max_connections() {
  local dhis2_server=$1 tomcat_remote=$2 concurrent_requests=$3 max_connections_list=$4 xmx_list=$5; file_with_urls=$6
  local host=$(echo $tomcat_remote | cut -d: -f1)
  local remote_tomcat_path=$(echo $tomcat_remote | cut -d: -f2-)
  
  echo -e "maxConnections\tXmx\tTime(ms)"

  for xmx in $xmx_list; do
    for max_connections in $max_connections_list; do
      local tomcat_final_conf=$(mktemp)
      local setenv_final_conf=$(mktemp)
      
      debug "Stop tomcat: $host"
      ssh "$host" "$remote_tomcat_path/bin/shutdown.sh" >&2

      debug "Set maxConnections=$max_connections, xmx=$xmx Mb"
      cat server.xml | MAX_CONNECTIONS=$max_connections envsubst > "$tomcat_final_conf"
      cat setenv.sh | XMX=$xmx envsubst > "$setenv_final_conf"
      debug "Copy tomcat configuration"
      rsync "$tomcat_final_conf" "$tomcat_remote/conf/server.xml"
      rsync "$setenv_final_conf" "$tomcat_remote/bin/setenv.sh"
      rm $tomcat_final_conf $setenv_final_conf

      debug "Start tomcat: $host"
      ssh "$host" "$remote_tomcat_path/bin/startup.sh" >&2
      debug "Wait for server: $dhis2_server"
      while ! curl -L --connect-timeout 5 --fail -q -u "admin:district" -sS "$dhis2_server" &>/dev/null; do
        sleep 1
      done
      debug "Server is up: $host"

      urls=$(cat $file_with_urls | xargs -i echo "$dhis2_server{}")
      elapsed=$(get_elapsed ab_for_urls $concurrent_requests $urls)
      echo -e "$max_connections\t$xmx\t$elapsed"
    done
  done

  debug "Stop tomcat: $host"
  ssh "$host" "$remote_tomcat_path/bin/shutdown.sh" >&2
}

main() {
  if test $# -lt  4; then
    debug "Usage: $(basename $0) DHIS2_SERVER REMOTE_URL CONCURRENT_REQUESTS MAX_CONNECTIONS_LIST XMX_LIST FILE_WITH_URLS"
    exit 2
  else
    benchmark_max_connections "$@"
  fi
}

main "$@"
