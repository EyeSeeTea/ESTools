#!/bin/bash
#set -x

# External Variables (to be set by the user)
export dhis2_instance=TEST
export db_server=localhost
export db_name=dhis2
export dump_dest_path="/path/to/backups"
export dump_remote_dest_path="/path/to/backups"
export db_user="db_user"
export db_pass="db_pass"
export DHIS2_HOME="/path/to/dhis2_home"

# Global variables
DB_REMOTE_DEST_SERVER=""
AUDIT=0
PERIOD_NAME=""
FORMAT="custom"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
NO_NAME="MANUAL"
BACKUP_NAME=""
DB_BACKUP_FILE=""
FILES_BACKUP_FILE=""

usage() {
    echo "~~~~~~~~~USAGE~~~~~~~~~~~~"
    echo "./backup_db.sh [NAME]"
    echo "./backup_db.sh [NAME] --periodicity [PERIOD] --format [FORMAT NAME] --destination [DESTINATION_HOST]"
    echo "Valid periods: day-in-week week-in-month month-in-year"
    echo "Valid formats: custom / plain"
    echo "Destination: host"
    echo "Example: ./backup_db.sh --periodicity day-in-week --format custom --destination gva11sucherubi.who.int"
    echo "If no PERIOD is given, then a manual dump is generated with timestamp, otherwise the given period is used in the name of the destination file."
}

get_timestamp() {
    echo $(date +%Y-%m-%d_%H%M)
}

assign_periodicity() {
    if [ "$1" = "day-in-week" ] || [ "$1" = "week-in-month" ] || [ "$1" = "month-in-year" ]; then
        BACKUP_NAME=""
        case $1 in
        day-in-week)
            PERIOD_NAME=$(date '+%A' | tr '[:upper:]' '[:lower:]')
            PERIOD_NAME="DAILY-$PERIOD_NAME"
            ;;
        week-in-month)
            PERIOD_NAME=$((($(date +%-d) - 1) / 7 + 1))
            case $PERIOD_NAME in
            1)
                PERIOD_NAME="WEEKLY-FIRST-WEEK"
                ;;
            2)
                PERIOD_NAME="WEEKLY-SECOND-WEEK"
                ;;
            3)
                PERIOD_NAME="WEEKLY-THIRD-WEEK"
                ;;
            4)
                PERIOD_NAME="WEEKLY-FOURTH-WEEK"
                ;;
            5)
                PERIOD_NAME="WEEKLY-FIFTH-WEEK"
                ;;
            esac
            ;;
        month-in-year)
            PERIOD_NAME=$(date +"%B" | tr '[:upper:]' '[:lower:]')
            PERIOD_NAME="MONTHLY-$PERIOD_NAME"
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
        FORMAT="$1"
    else
        echo "ERROR: invalid format"
        usage
        exit 1
    fi
}

assign_destination() {
    if [ "$1" != "" ]; then
        DB_REMOTE_DEST_SERVER="$1"
    else
        echo "Error, destination is empty"
        usage
        exit 1
    fi
}

assign_params() {
    while [ "$1" != "" ]; do
        case $1 in
        -p | --periodicity)
            assign_periodicity "$2"
            shift 2
            ;;
        -f | --format)
            assign_format "$2"
            shift 2
            ;;
        -d | --destination)
            assign_destination "$2"
            shift 2
            ;;
        --exclude-audit)
            AUDIT=1
            shift
            ;;
        *)
            assign_name "$1"
            shift
            ;;
        esac
    done
}

assign_name() {
    local backup_name=$1
    BACKUP_NAME=${backup_name}
}

success() {
    echo OK
}

fail() {
    local status=$1

    echo FAIL
    exit "$status"
}

backup_dhis2_folders() {
    local dhis2_home=$1 backup_file_base=$2
    local backup_file

    backup_file="${backup_file_base}_dhis2_files.tar.gz"
    FILES_BACKUP_FILE="${backup_file}"

    echo "[$(get_timestamp)] Generating DHIS2 files backup into ${backup_file}..."
    tar --exclude="files/apps" -C "$dhis2_home" -czf "${dump_dest_path}/${backup_file}" "files" "static"
}

backup_db() {
    local backup_file_base=$1
    local pg_dump_opts_base pgdump_opts backup_file

    pg_dump_opts_base=(
        --no-owner
        --exclude-table 'aggregated*'
        --exclude-table 'analytics*'
        --exclude-table 'completeness*'
        --exclude-schema sys
    )

    pgdump_opts=("${pg_dump_opts_base[@]}")

    if [ $AUDIT -eq 1 ]; then
        pgdump_opts+=(--exclude-table audit)
    fi

    if [ "$FORMAT" = "custom" ]; then
        backup_file="${backup_file_base}_cformat.dump"
        DB_BACKUP_FILE="${backup_file}"
        echo "[$(get_timestamp)] Generating custom backup into ${backup_file}..."
        pg_dump -d "postgresql://${db_user}:${db_pass}@${db_server}:5432/${db_name}" "${pgdump_opts[@]}" -f "${dump_dest_path}/${backup_file}" -Fc
    else
        backup_file="${backup_file_base}.sql.tar.gz"
        DB_BACKUP_FILE="${backup_file}"
        echo "[$(get_timestamp)] Generating plain backup into ${backup_file}"
        pg_dump -d "postgresql://${db_user}:${db_pass}@${db_server}:5432/${db_name}" "${pgdump_opts[@]}" -Fp | gzip >"${dump_dest_path}/${backup_file}"
    fi
}

copy_backup_to_remote() {
    local db_backup_file=$1 file_backup_file=$2

    echo "[$(get_timestamp)] CP backup into ${DB_REMOTE_DEST_SERVER}..."
    scp "${dump_dest_path}/${db_backup_file}" "${dump_dest_path}/${file_backup_file}" "${DB_REMOTE_DEST_SERVER}:${dump_remote_dest_path}"
}

backup() {
    local backup_file_base

    if [ "$BACKUP_NAME" = "" ] && [ "$PERIOD_NAME" = "" ]; then
        BACKUP_NAME=$NO_NAME
        BACKUP_NAME="-${BACKUP_NAME}-${TIMESTAMP}"
    fi
    backup_file_base="BACKUP-${dhis2_instance}-${PERIOD_NAME}${BACKUP_NAME}"
    echo "${backup_file_base}"

    if backup_db "$backup_file_base"; then
        success
    else
        fail 1
    fi

    echo "${backup_file_base}"
    if backup_dhis2_folders "$DHIS2_HOME" "${backup_file_base}"; then
        success
    else
        fail 3
    fi

    echo "$DB_BACKUP_FILE" "$FILES_BACKUP_FILE"
    if [[ ! "$DB_REMOTE_DEST_SERVER" == "" ]]; then
        if copy_backup_to_remote "$DB_BACKUP_FILE" "$FILES_BACKUP_FILE"; then
            success
        else
            fail 2
        fi
    else
        exit 0
    fi
}

main() {
    if [ "$#" = "0" ]; then
        backup
        exit 0
    fi

    if [ "$#" = "1" ]; then
        if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
            usage
            exit 0
        else
            assign_name "$1"
            backup
            shift
            exit 0
        fi
    fi

    if [ "$#" -gt 1 ]; then
        assign_params "$@"
        backup
    else
        usage
        exit 1
    fi
}

main "$@"
exit 0
