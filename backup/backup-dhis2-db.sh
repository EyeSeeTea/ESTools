#!/bin/bash

# Backup a postgres DHIS2 database. Tasks:
#
#    - Dump database in custom format (-Fc) without aggregated/analytics/completeness tables.
#
#    - Delete files older than:
#        - a week (when period == 'daily')
#        - a month (when period == 'weekly')
#        - a year (when period == 'yearly')

set -e -u -o pipefail

declare -A days_by_period=([daily]=7 [weekly]=31 [monthly]=365)

debug() {
    echo "$@" >&2
}

dump_database() {
    local db_uri=$1 dump_path=$2
    debug "[${timestamp}] Dump database: ${dump_path}"

    pg_dump -d "${db_uri}" \
        --no-owner \
        --exclude-table 'aggregated*' \
        --exclude-table 'analytics*' \
        --exclude-table 'completeness*' \
        --exclude-schema sys \
        -Fc \
        -f "${dump_path}"
}

delete_old_files() {
    local period=$1 dump_dest_path=$2
    local days=${days_by_period[$period]}
    debug "Delete files older than ${days} days: ${dump_dest_path}"
    find "${dump_dest_path}" -mtime "+$days" -print0 | xargs -0 -r -t -n1 rm
}

backup() {
    local db_uri=$1 backups_path=$2 period=$3

    if ! test "$period" = "daily" -o "$period" = "weekly" -o "$period" = "monthly"; then
        debug "Invalid period: $period"
        return 1
    fi

    local timestamp dump_dest_path backup_file dump_path
    timestamp=$(date +%Y-%m-%d_%H%M)
    dump_dest_path=$backups_path/$period
    backup_file="backup-${period}-$timestamp.dump"
    dump_path=${dump_dest_path}/${backup_file}

    mkdir -p "$dump_dest_path"
    delete_old_files "$period" "$dump_dest_path"
    dump_database "$db_uri" "$dump_path"

    echo "${dump_path}"
}

if [ $# -lt 3 ]; then
    debug "Usage: $(basename "$0") DB_URI DESTINATION_DIR daily|weekly|monthly"
else
    backup "$@"
fi
