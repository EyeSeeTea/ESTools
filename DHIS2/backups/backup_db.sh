#!/bin/sh
#set -x

#config options
dhis2_instance=
db_server=
db_user=
db_pass=
db_name=
dump_dest_path=
dump_remote_dest_path=

####
db_remote_dest_server=""
fail=0
period_name=""
format="c"
timestamp=$(date +%Y-%m-%d_%H%M)
no_name="MANUAL"
backup_name=""

usage() {
  echo "~~~~~~~~~USAGE~~~~~~~~~~~~"
  echo "./backup_db.sh [NAME]"
  echo "./backup_db.sh [NAME] --periodicity [PERIOD] --format [FORMAT NAME] --destine [DESTINE_HOST]"
  echo "Valid periods: day-in-week week-in-month month-in-year"
  echo "Valid formats: custom / plain"
  echo "Destine: host"
  echo "Example: ./backup_db.sh --periodicity day-in-week --format custom --destine gva11sucherubi.who.int"
  echo "If no PERIOD is given, then a manual dump is generated with timestamp, otherwise the given period is used in the name of the destination file."
}

assign_periodicity() {
  if [ "$1" = "day-in-week" ] || [ "$1" = "week-in-month" ] || [ "$1" = "month-in-year" ]; then
    backup_name=""
    case $1 in
    day-in-week)
      period_name=$(date '+%A' | tr 'a-z' 'A-Z')
      period_name=$period_name
      ;;
    week-in-month)
      period_name=$((($(date +%-d) - 1) / 7 + 1))
      case $period_name in
      1)
        period_name="FIRST-WEEK-"
        ;;
      2)
        period_name="SECOND-WEEK-"
        ;;
      3)
        period_name="THIRD-WEEK-"
        ;;
      4)
        period_name="FOURTH-WEEK-"
        ;;
      esac
      ;;
    month-in-year)
      period_name=$(date +"%B" | tr 'a-z' 'A-Z')
      period_name=$period_name"-MONTH-"
      ;;
    esac

  else
    echo "ERROR: invalid period"
    usage
    exit 1
  fi
}

assign_format() {
  if [ "$1" = "custom" ] || [ "$1" = "plain" ]; then
    format="$1"
  else
    echo "ERROR: invalid format"
    usage
    exit 1
  fi
}

assign_destine() {
  if [ "$1" != "" ]; then
    db_remote_dest_server="$1"
  else
    echo "Error, destine is empty"
    usage
    exit 1
  fi
}

assign_params() {
  while [ "$1" != "" ]; do
    case $1 in
    -p | --periodicity)
      assign_periodicity $2
      shift 2
      ;;
    -f | --format)
      assign_format $2
      shift 2
      ;;
    -d | --destine)
      assign_destine $2
      shift 2
      ;;
    *)
      assign_name $1
      shift
      ;;
    esac
  done
}

assign_name() {
  backup_name=$1
  backup_name=${backup_name}
}

check_status() {
  if [ $? -eq 0 ]; then
    echo OK
  else
    echo FAIL
    fail=$1
    exit $1
  fi
}

backup() {
  if [ "$backup_name" = "" ] && [ "$period_name" = "" ]; then
    backup_name=$no_name
    backup_name=${backup_name}-${timestamp}
  fi

  backup_file=BACKUP-${dhis2_instance}-${period_name}-${backup_name}
  if [ "$format" = "c" ]; then
    backup_file="${backup_file}_cformat.dump"
    echo "[${timestamp}] Generating custom backup into ${backup_file}..."
    pg_dump -d "postgresql://${db_user}:${db_pass}@${db_server}:5432/${db_name}" --no-owner --exclude-table 'aggregated*' --exclude-table 'analytics*' --exclude-table 'completeness*' --exclude-schema sys -f ${dump_dest_path}/${backup_file} -Fc
  else
    backup_file="${backup_file}.sql.tar.gz"
    echo "[${timestamp}] Generating plain backup into ${backup_file}"
    pg_dump -d "postgresql://${db_user}:${db_pass}@${db_server}:5432/${db_name}" --no-owner --exclude-table 'aggregated*' --exclude-table 'analytics*' --exclude-table 'completeness*' --exclude-schema sys -Fp | gzip > ${dump_dest_path}/${backup_file}
  fi

  check_status 1
  if [ "$db_remote_dest_server" != "" ]; then
    exit 0
  fi
  if [ "$fail" = 0 ]; then
    echo "[${timestamp}] CP backup into ${db_remote_dest_server}..."
    scp ${dump_dest_path}/${backup_file} ${db_remote_dest_server}:${dump_remote_dest_path}
    check_status 2
  fi
}

main() {
  if [ "$#" = "0" ]; then
    backup
    exit 0
  fi
  if [ "$#" = "1" ]; then
    if [ "$1" == "-h" ] | [ "$1" == "--help" ]; then
      usage
      exit 0
    else
      assign_name $1
      backup
      shift
      exit 0
    fi
  fi
  if [ "$#" -gt 1 ]; then
    assign_params $@
    backup
  else
    usage
    exit 1
  fi
}

main $@
exit 0
