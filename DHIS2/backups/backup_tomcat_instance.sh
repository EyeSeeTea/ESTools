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
SKIP_AUDIT=0
SKIP_FILES=0
PERIOD_NAME=""
FORMAT="custom"
TIMESTAMP=""
MANUAL_BACKUP="MANUAL"
BACKUP_NAME=""
DB_BACKUP_FILE=""
FILES_BACKUP_FILE=""

# Error messages
INVALID_OPTION="ERROR: invalid option or missing argument at:"
INVALID_FORMAT="ERROR: invalid format:"
INVALID_PERIOD="ERROR: invalid period:"
INVALID_DESTINATION="ERROR: invalid destination:"

error() {
    local message=$1

    echo "$message" >&2
}

unknown_option() {
    local message=$1 option=$2

    if [ -z "$option" ]; then
        option="no option specified"
    fi

    error "$message $option"
    error "use -h or --help for help"
    exit 1
}

# Usage
formatted_print() {
    local text=$1 width=$2
    width=${width:-80}

    echo "$text" | fold -s -w "$width"
}

usage() {
    formatted_print "Usage: backup_db.sh"
    formatted_print "or:    backup_db.sh --name [NAME] --periodicity [PERIOD] --format [FORMAT NAME] --destination [DESTINATION_HOST]"
    formatted_print ""
    formatted_print "Make a backup of the DHIS2 database and files."
    formatted_print "If no PERIOD is given, then a manual dump is generated with timestamp as period, otherwise the given period is used in the name of the destination file."
    formatted_print "The backup name is composed by: BACKUP-DHIS2_INSTANCE-PERIOD-NAME"
    formatted_print ""
    formatted_print "Options:"
    formatted_print "-p, --periodicity [day-in-week | week-in-month | month-in-year]: Used in scheduled backups to add a period identifier to the backup name. If not set the backup is created with a MANUAL-TIMESTAMP suffix."
    formatted_print "-f, --format [custom | plain]: Type of format used in pg_dump, custom means -Fc and plain means a compressed -Fp."
    formatted_print "-d, --destination [DESTINATION_HOST]: Remote host where the backup will be copied."
    formatted_print "--exclude-audit: Exclude the audit table from the backup."
    formatted_print "--exclude-files: Exclude the DHIS2 files from the backup."
    formatted_print ""
    formatted_print "Example: ./backup_db.sh --periodicity day-in-week --format custom --destination hostname.example"
}

get_timestamp() {
    date +%Y-%m-%d_%H%M
}

TIMESTAMP=$(get_timestamp)

assign_periodicity() {
    if [ "$1" = "day-in-week" ] || [ "$1" = "week-in-month" ] || [ "$1" = "month-in-year" ]; then
        case $1 in
        day-in-week)
            PERIOD_NAME=$(date '+%A' | tr '[:upper:]' '[:lower:]')
            PERIOD_NAME="DAILY-${PERIOD_NAME}"
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
            PERIOD_NAME="MONTHLY-${PERIOD_NAME}"
            ;;
        esac

    else
        unknown_option "$INVALID_PERIOD" "$1"
    fi
}

assign_format() {
    if [ "$1" = "custom" ] || [ "$1" = "plain" ]; then
        FORMAT="$1"
    else
        unknown_option "$INVALID_FORMAT" "$1"
    fi
}

assign_destination() {
    if [ "$1" != "" ]; then
        DB_REMOTE_DEST_SERVER="$1"
    else
        unknown_option "$INVALID_DESTINATION" "$1"
    fi
}

process_options() {
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
        -n | --name)
            assign_name "$2"
            shift 2
            ;;
        --exclude-audit)
            SKIP_AUDIT=1
            shift
            ;;
        --exclude-files)
            SKIP_FILES=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -?* | *)
            unknown_option "$INVALID_OPTION" "$1"
            ;;
        esac

    done
}

assign_name() {
    local backup_name=$1
    BACKUP_NAME="-${backup_name}"
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
    tar --exclude="files/apps" -C "${dhis2_home}" -czf "${dump_dest_path}/${backup_file}" "files" "static"
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

    if [ $SKIP_AUDIT -eq 1 ]; then
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
    local db_path="${dump_dest_path}/${db_backup_file}" files_path

    if [ "$file_backup_file" != "" ]; then
        files_path+=" ${dump_dest_path}/${file_backup_file}"
    fi

    echo "[$(get_timestamp)] CP backup into ${DB_REMOTE_DEST_SERVER}..."
    scp "${db_path}" "${files_path}" "${DB_REMOTE_DEST_SERVER}:${dump_remote_dest_path}"
}

backup() {
    local backup_file_base

    if [ "$BACKUP_NAME" = "" ] && [ "$PERIOD_NAME" = "" ]; then
        BACKUP_NAME="-${MANUAL_BACKUP}"
    fi

    if [ "$PERIOD_NAME" = "" ]; then
        PERIOD_NAME="${TIMESTAMP}"
    fi

    backup_file_base="BACKUP-${dhis2_instance}-${PERIOD_NAME}${BACKUP_NAME}"

    if backup_db "${backup_file_base}"; then
        success
    else
        fail 1
    fi

    if [ $SKIP_FILES -eq 0 ]; then
        if backup_dhis2_folders "${DHIS2_HOME}" "${backup_file_base}"; then
            success
        else
            fail 3
        fi
    fi

    if [[ ! "$DB_REMOTE_DEST_SERVER" == "" ]]; then
        if copy_backup_to_remote "${DB_BACKUP_FILE}" "${FILES_BACKUP_FILE}"; then
            success
        else
            fail 2
        fi
    else
        exit 0
    fi
}

main() {
    if [ "$#" -gt 0 ]; then
        process_options "$@"
    fi

    backup
}

main "$@"
exit 0
