#!/bin/sh
#set -x

timestamp=$(date +%Y-%m-%d_%H%M)
period=

if [ $# -gt 1 ]; then
  echo "wrong parameter number" 
  exit 1
elif [ $# -eq 1 ]; then
  if [ "$1" == "-h" -o "$1" == "--help" ]; then
    echo "USAGE: ./backup_db.sh [PERIOD]" 
    echo "If no PERIOD is given, then a manual dump is generated with timestamp, otherwise the given period is used in the name of the destination file." 
    exit
  fi
  period=$1
else
  period=MANUAL-${timestamp}
fi

dhis2_instance=XXX
db_server=xxxxx.xxx.xxx
db_user=xxxxxx
db_pass=xxxxxxxx
db_name=xxxxxx
dump_dest_path=/xxxxxxxx/xxxxx

check_status(){
check_status(){
    if [ $? -eq 0 ]; then
        echo OK
    else
        echo FAIL
    fi
}

backup_file=BACKUP-${dhis2_instance}-${period}_cformat.dump
echo "[${timestamp}] Generating backup into ${backup_file}..." 
pg_dump -d "postgresql://${db_user}:${db_pass}@${db_server}:5432/${db_name}" --no-owner --exclude-table 'aggregated*' --exclude-table 'analytics*' --exclude-table 'completeness*' --exclude-schema sys -Fc -f ${dump_dest_path}/${backup_file}
check_status
