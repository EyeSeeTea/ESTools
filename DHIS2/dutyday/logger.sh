#!/bin/bash
#this file must be placed in the instances
set +x

monitlogger() {
  echo ""
	echo "----------monitlog----------"
	echo
	sudo monit status | awk '/Process/{p=$0} /Not monitored/{print p "\n" $0 "\n"}'
	echo
}


databaselogger() {
    echo ""
    echo -e "--------databaselog-----------"
	  echo
    local file=$1
    tail -10 $file 2>&1
    echo ""
}

clonelogger(){
    local file=$1
    echo ""
	  echo "--------------clone log--------------------"
	  echo
    echo ""
    echo "loading $file"
    echo ""
    START_DATE=$(date -d 'last Saturday' '+%Y-%m-%d')
    echo $START_DATE
    echo "awk '/$START_DATE/{flag=1} flag' $file | grep 'ERROR\|error\|FAIL\|Error\|OK\|$START_DATE' | sed  's/\'[^:]*:[^\']*\'/USER:PASSWORDHIDDEN/g'"
    awk "/$START_DATE/{flag=1} flag" $file | grep  "ERROR\|error\|FAIL\|Error\|OK\|$START_DATE" | sed  "s/'[^:]*:[^']*'/USER:PASSWORDHIDDEN/g "
    echo ""
    echo "end of resume clone log"
    echo ""
}


analyticslogger() {
    local type=$1
    local host=$2
    local file=$3
    echo
    echo "--------------Analytics log--------------------"
    echo

    echo "Executing analyticsloger: $type file: $file host: $host"

    LOG_FILE=$file
    if [ $type == "docker" ];then
      dockerid=$(docker ps | grep $host"-core" | awk '{print $1}')

      response=$(docker cp $dockerid +":"+$file+" /backup/logs/.")
      file=$(basename $file)
      LOG_FILE="/backup/logs/$file"
    fi
    DAYS_BACK=2

    # Calculates the start date based on days back
    START_DATE=$(date -d"-2 days" +%Y-%m-%d)+"|"+$(date -d"-1 days" +%Y-%m-%d)+"|"+$(date -d"-0 days" +%Y-%m-%d)

    START_LINE=$(grep -E "$START_DATE" $LOG_FILE | grep 'Table update start: analytics, earliest:'| grep 'last years=500')
    END_LINE=`grep -E "$START_DATE" $LOG_FILE | grep 'Analytics tables updated' | grep -v ' 00:0'`
    ERROR_LINES=$(grep -E "$START_DATE" $LOG_FILE | grep 'ERROR')
    printf "%s" "$START_LINE$END_LINE$ERROR_LINES" | awk '{gsub("T"," ",$3); print}' | sort -k3,3 -k4,4

    echo
    echo "Fin del proceso 'analytics':"
    echo
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
    *)
        echo "Comando desconocido: $command"
        exit 1
        ;;
esac