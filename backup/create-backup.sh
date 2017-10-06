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

export_mysql() { local root_password=$1 output_dump_path=$2
  debug "Exporting mysql DB: $output_dump_path"
  mysqldump -u root --password="$root_password" --single-transaction --all-databases > "$output_dump_path"
}

export_postgres() { local postgres_password=$1 output_dump_path=$2
  debug "Exporting postgres DB: $output_dump_path"
  PGPASSWORD="$postgres_password" pg_dumpall -U postgres > "$output_dump_path"
}

create_directory() { local output_dir=$1
  debug "Create output dir: $output_dir"
  mkdir -p "$output_dir"
}

sync_backup() { local output_dir=$1 rdiff_destination=$2
  debug "Copying files $output_dir -> $rdiff_destination"
  rdiff-backup "$output_dir/" "$rdiff_destination"
  rdiff-backup --remove-older-than "1Y" "$rdiff_destination"
}

backup_files() { local files_from=$1 output_dir=$2
  rsync --quiet -avP --delete --recursive --delete-excluded \
    --files-from=<(cat "$files_from" | grep -v "^-") \
    --exclude-from=<(cat "$files_from" | grep "^-") \
    / "$output_dir/files"
}

main() {
  local usage args output_dir
  local mysql_password output_dir_arg rdiff_destination files_from

  usage="Usage: $(basename "$0") [OPTIONS]
    OPTIONS:
      -h | --help -- Show this help message

      -o OUTPUT_DIRECTORY | --output_dir=OUTPUT_DIRECTORY -- Set output directoy [default: ./output]
      --files-from=PATH -- Get file/directories to include in the back from PATH
      -r RSYNC_URI | --destination=RSYNC_URI - Rsync URI to copy the backup to

      --mysql-password=PASS -- MySQL password
      --postgres-password=PASS -- PostgreSQL password"

  args="$(getopt \
    -o "ho:r:" \
    -l "help,output-dir:,files-from:,destination:,mysql-password:,postgres-password:" \
    --name "$0" -- "$@")"

  eval set -- "$args"

  while true; do
    case "$1" in
      --mysql-password) mysql_password=$2; shift 2;;
      --postgres-password) postgres_password=$2; shift 2;;
      -o|--output-dir) output_dir_arg=$2; shift 2;;
      --files-from) files_from=$2; shift 2;;
      -r|--destination) rdiff_destination=$2; shift 2;;
      -h|--help) debug "$usage"; exit;;
      --) shift; break;;
      *) die "Not implemented: $1";;
    esac
  done

  output_dir=$(test "${output_dir_arg+set}" && echo "$output_dir_arg" || mktemp -d)

  create_directory "$output_dir"

  test "${files_from+set}" &&
    backup_files "$files_from" "$output_dir"

  test "${mysql_password+set}" &&
    export_mysql "$mysql_password" "$output_dir/mysql-dump.sql"

  test "${postgres_password+set}" &&
    export_postgres "$postgres_password" "$output_dir/postgres-dump.sql"

  test "${rdiff_destination+set}" &&
    sync_backup "$output_dir" "$rdiff_destination"

  ! test "${output_dir_arg+set}" &&
    rm -rf "$output_dir"
}

main "$@"