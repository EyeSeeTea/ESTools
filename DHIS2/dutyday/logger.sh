#!/bin/bash
#this file must be placed in the instances
set +x

test_connection() {
    local servername=$1
    echo "$servername connected"
}

githubupdater() {
    local file=$1
    local branch=$2
    local command="${file}githubupdater.py"
    export http_proxy=$3
    export https_proxy=$3
    echo "Running githubupdater: file: $file branch: $branch command=$command"
    python3 "$command" "$file" "$branch"
    echo "Github update finished"
}

monitlogger() {
    sudo monit status | awk '/Process/{p=$0} /Not monitored/{print p "\n" $0 "\n"}'
}

databaselogger() {
    local file=$1
    tail -10 "$file" 2>&1
}

catalinaerrors() {
    local file=$1
    grep "ERROR" "$file" | grep -v "Unable to render velocity template"
}

dockerharborclonelogger() {
    local file=$1
    TODAY=$(date '+%Y-%m-%d')
    awk "/$TODAY/{flag=1} flag" "$file" | sed "s/'[^:]*:[^']*'/USER:PASSWORDHIDDEN/g "
}

clonelogger() {
    local file=$1
    START_DATE=$(date -d 'last Saturday' '+%Y-%m-%d')
    NEXT_DAY=$(date -d "$START_DATE + 1 day" '+%Y-%m-%d')
    echo "$START_DATE"
    awk "/$START_DATE/{flag=1} flag" "$file" | grep "ERROR\|error\|FAIL\|Error\|OK\|$START_DATE" | sed "s/'[^:]*:[^']*'/USER:PASSWORDHIDDEN/g "
    echo "$NEXT_DAY"
    awk "/$NEXT_DAY/{flag=1} flag" "$file" | grep "ERROR\|error\|FAIL\|Error\|OK\|$NEXT_DAY" | sed "s/'[^:]*:[^']*'/USER:PASSWORDHIDDEN/g "
}

analyticslogger() {
    local type=$1
    local file=$2
    local host=$3

    LOG_FILE=$file
    if [ "$type" == "docker" ]; then
        dockerid=$(docker ps | grep "$host""-core" | awk '{print $1}')
        if [[ -n $dockerid ]]; then
            docker cp "${dockerid}:${file}" /tmp/
            file=$(basename "$file")
            LOG_FILE="/tmp/$file"
        else
            echo "docker id not found"
            exit 1
        fi
    fi

    START_DATE=$(date -d"-2 days" +%Y-%m-%d)+"|"+$(date -d"-1 days" +%Y-%m-%d)+"|"+$(date -d"-0 days" +%Y-%m-%d)

    START_LINE=$(grep -E "$START_DATE" "$LOG_FILE" | grep 'Table update start: analytics, earliest:' | grep -E 'last years=500|last years=100')
    END_LINE=$(grep -E "$START_DATE" "$LOG_FILE" | grep 'Analytics tables updated' | grep -v ' 00:0')
    ERROR_LINES=$(grep -E "$START_DATE" "$LOG_FILE" | grep 'ERROR')
    printf "%s" "$START_LINE$END_LINE$ERROR_LINES" | awk '{gsub("T"," ",$3); print}' | sort -k3,3 -k4,4
}
# Script starts here
if [ $# -eq 0 ]; then
    echo ""
    echo "Arguments not provided"
    exit 1
fi

command=$1
shift
case $command in
monitlogger)
    monitlogger "$@"
    ;;
analyticslogger)
    analyticslogger "$@"
    ;;
databaselogger)
    databaselogger "$@"
    ;;
clonelogger)
    clonelogger "$@"
    ;;
githubupdater)
    githubupdater "$@"
    ;;
test_connection)
    test_connection "$@"
    ;;
catalinaerrors)
    catalinaerrors "$@"
    ;;
dockerharborclonelogger)
    dockerharborclonelogger "$@"
    ;;

*)
    echo "Command not found: $command"
    exit 1
    ;;
esac
