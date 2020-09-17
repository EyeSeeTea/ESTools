#!/bin/bash
set -e -u

# Run WAR on port and debug on (port - 1000)
jetty_runner() { local war_path=$1 port=$2; shift 2
    debug_port=$((port - 1000))
    debug_opts="-Xdebug -Xrunjdwp:transport=dt_socket,address=$debug_port,server=y,suspend=n"
    DHIS2_HOME=$(dirname "$warfile") java \
        $debug_opts \
        -jar /usr/local/bin/jetty-runner.jar \
        --port $port \
        "$@" "$war_path"
}

main() {
    if test $# -ne 2; then
        echo "Usage: $(basename "$0") DHIS_WAR_PATH SERVER_PORT"
        exit 1
    fi

    local warfile=$1 port=$2
    jetty_runner "$warfile" "$port"
}

main "$@"
