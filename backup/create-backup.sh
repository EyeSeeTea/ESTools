#!/bin/bash
#
# Create incremental backups for MySQL, PostgresSQL and files.
#
# Dependencies: rsync, rdiff-backup
#
set -e -u -o pipefail

stderr() { echo -e "$@" >&2; }

debug() { stderr "[$(date +%Y-%m-%d_%H-%M-%S)] $@"; }

die() { debug "$@" && exit 1; }

export_mysql() { local output_dump_path=$1
  debug "Export mysql DB: $output_dump_path"
  mysqldump --single-transaction --all-databases > "$output_dump_path"
}

export_postgres() { local output_dump_path=$1
  debug "Export postgres DB: $output_dump_path"
  pg_dumpall -U postgres > "$output_dump_path"
}

create_directory() { local temporal_dir=$1
  debug "Create temporal directory: $temporal_dir"
  mkdir -p "$temporal_dir"
}

sync_backup() { local temporal_dir=$1 rdiff_destination=$2
  debug "Sync: $temporal_dir -> $rdiff_destination"
  rdiff-backup "$temporal_dir/" "$rdiff_destination"
  rdiff-backup --force --remove-older-than "1M" "$rdiff_destination"
}

backup_files() { local files_from=$1 temporal_dir=$2
  debug "Backup files and directories ($files_from) to $temporal_dir"
  rsync --quiet -avP --delete --recursive --delete-excluded \
    --files-from=<(cat "$files_from" | grep -v "^-") \
    --exclude-from=<(cat "$files_from" | grep "^-") \
    / "$temporal_dir/files"
}

delete_directory() { local dir=$1
  debug "Remove directory: $dir"
  test "$dir" && rm -rf "$dir"
}

main() {
  local usage args temporal_dir
  local mysql postgres temporal_dir_arg rdiff_destination files_from

  usage="Usage: $(basename "$0") [OPTIONS]
    OPTIONS:
      -h | --help -- Show this help message

      -t TEMPORAL_DIRECTORY | --temporal_dir=TEMP_DIRECTORY -- Set temporal directory
      --files-from=PATH -- Get file/directories to include in the back from PATH
      -r RSYNC_URI | --destination=RSYNC_URI - Rsync URI to copy the backup to

      --mysql -- Export MySQL databases
      --postgres -- Export PostgreSQL databases"

  args="$(getopt \
    -o "ht:r:" \
    -l "help,temporal-dir:,files-from:,destination:,mysql,postgres" \
    --name "$0" -- "$@")"

  eval set -- "$args"

  while true; do
    case "$1" in
      -t|--temporal-dir) temporal_dir_arg=$2; shift 2;;
      -r|--destination) rdiff_destination=$2; shift 2;;
      -h|--help) debug "$usage"; exit;;
      --mysql) mysql=1; shift 1;;
      --postgres) postgres=1; shift 1;;
      --files-from) files_from=$2; shift 2;;
      --) shift; break;;
      *) die "Not implemented: $1";;
    esac
  done

  temporal_dir=$(test "${temporal_dir_arg+set}" && echo "$temporal_dir_arg" || mktemp -d)

  create_directory "$temporal_dir"

  test "${files_from+set}" &&
    backup_files "$files_from" "$temporal_dir"

  test "${mysql+set}" &&
    export_mysql "$temporal_dir/mysql-dump.sql"

  test "${postgres+set}" &&
    export_postgres "$temporal_dir/postgres-dump.sql"

  test "${rdiff_destination+set}" &&
    sync_backup "$temporal_dir" "$rdiff_destination"

  ! test "${temporal_dir_arg+set}" &&
    delete_directory "$temporal_dir"
}

main "$@"
