#!/bin/sh
set -e -u -o pipefail

main() {
  if test $# -ne 2; then
    echo "Usage: $(basename "$0") DHIS_WAR_PATH SERVER_PORT"
  else
    local scriptdir=$(dirname "$(readlink -f "$0")")
    local warfile=$1 port=$2
    DHIS2_HOME=$(dirname "$warfile") \
      exec java -jar $scriptdir/jetty-runner.jar --port $port "$warfile"
  fi
}

main "$@"
