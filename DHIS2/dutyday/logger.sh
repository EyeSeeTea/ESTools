#!/bin/bash
#this file must be placed in the instances
set +x

logger_file="dutyday/logger.sh"

githubupdater() {
    local url=$1
    local branch=$2
    echo "Running githubupdater: $url $branch"
    echo "python githubupdater.py $url $branch"
    python githubupdater.py --repo_path $url --branch $branch
}

monitlogger() {
	sudo monit status | awk '/Process/{p=$0} /Not monitored/{print p "\n" $0 "\n"}'
}


databaselogger() {
    local file=$1
    tail -10 $file 2>&1
}

clonelogger(){
    local file=$1
    START_DATE=$(date -d 'last Saturday' '+%Y-%m-%d')
    echo $START_DATE
    awk "/$START_DATE/{flag=1} flag" $file | grep  "ERROR\|error\|FAIL\|Error\|OK\|$START_DATE" | sed  "s/'[^:]*:[^']*'/USER:PASSWORDHIDDEN/g "
}


analyticslogger() {
    local type=$1
    local host=$2
    local file=$3
    
    LOG_FILE=$file
    if [ $type == "docker" ];then
      dockerid=$(docker ps | grep $host"-core" | awk '{print $1}')

      response=$(docker cp $dockerid +":"+$file+" /backup/logs/.")
      file=$(basename $file)
      LOG_FILE="/backup/logs/$file"
    fi
    DAYS_BACK=2

    START_DATE=$(date -d"-2 days" +%Y-%m-%d)+"|"+$(date -d"-1 days" +%Y-%m-%d)+"|"+$(date -d"-0 days" +%Y-%m-%d)

    START_LINE=$(grep -E "$START_DATE" $LOG_FILE | grep 'Table update start: analytics, earliest:'| grep 'last years=500')
    END_LINE=`grep -E "$START_DATE" $LOG_FILE | grep 'Analytics tables updated' | grep -v ' 00:0'`
    ERROR_LINES=$(grep -E "$START_DATE" $LOG_FILE | grep 'ERROR')
    printf "%s" "$START_LINE$END_LINE$ERROR_LINES" | awk '{gsub("T"," ",$3); print}' | sort -k3,3 -k4,4
}
# Main del script
if [ $# -eq 0 ]; then
    echo ""
    echo "No se proporcionaron argumentos"
    exit 1
fi

command=$1
shift
case $command in
    monitlogger)
        monitlogger $@
        ;;
    analyticslogger)
        analyticslogger $@
        ;;
    databaselogger)
        databaselogger $@
        ;;
    clonelogger)
        clonelogger $@
        ;;
    githubupdater)
        githubupdater $@
        ;;
    *)
        echo "Comando desconocido: $command"
        exit 1
        ;;
esac