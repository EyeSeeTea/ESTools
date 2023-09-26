#!/bin/bash

set -e -u -o pipefail

USAGE="Usage: $(basename "$0") dhisconf_path docker_name"

get_conf_field() {
    local conf_file=$1 field=$2
    echo $(grep -e "^$field" "$conf_file" | awk -F '= ' '{print $2}' | tr -d '[:space:]')
}

parse_dburl() {
    local url=$1

    local host port dbname

    local pattern="jdbc:postgresql://([^:/]+):([0-9]+)/([^/]+)"

    if [[ $url =~ $pattern ]]; then
        host="${BASH_REMATCH[1]}"
        port="${BASH_REMATCH[2]}"
        dbname="${BASH_REMATCH[3]}"

        echo "$host $port $dbname"
    fi
}

delete_spam_tomcat() {
    local conf_file=$1

    local host port dbname dbuser password

    read -r host port dbname <<<"$(parse_dburl "$(get_conf_field "$conf_file" "connection.url")")"
    dbuser=$(get_conf_field "$conf_file" "connection.username")
    password=$(get_conf_field "$conf_file" "connection.password")

    python3 /home/tomcatuser/bin/delete_spam.py --dsn "host=$host port=$port password=$password dbname=$dbname user=$dbuser"
}

delete_spam_docker() {
    local conf_file=$1 docker_name=$2

    local docker_id docker_port dburl dbname dbuser

    docker_id=$(docker ps --format "{{.ID}}" --filter "name=$docker_name")
    docker_port=$(docker port "$docker_id" 1000/tcp | awk -F':' '{print $2}')

    dburl=$(get_conf_field "$conf_file" "connection.url")
    dbname="${dburl##*/}"
    dbuser=$(get_conf_field "$conf_file" "connection.username")

    local nc_cmd="nc -lk -p 1000 -e nc localhost 5432"

    docker exec -i "$docker_id" bash -c "$nc_cmd" &
    local tunel_PID=$!

    python3 ./delete_spam.py --dsn "host=localhost port=$docker_port dbname=$dbname user=$dbuser"

    kill "$tunel_PID"
    docker exec -i "$docker_id" bash -c "pkill -f "$nc_cmd""
}

delete_spam() {
    local conf_file=$1 docker_name=$2

    if [ -n "$docker_name" ]; then
        delete_spam_docker "$conf_file" "$docker_name"
    else
        delete_spam_tomcat "$conf_file"
    fi
}

if [ $# -lt 1 ]; then
    echo "$USAGE"
    exit 1
else
    delete_spam "$@"
fi
