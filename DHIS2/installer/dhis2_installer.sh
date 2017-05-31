#!/bin/bash
set -e -u -o pipefail

# Bash set options:
#   -e          -- Exit when any command fails
#   -u          -- Exit when the script uses an undefined variable
#   -o pipefail -- Exit when a command in a pipe fails
#   -o posix    -- Enable Posix mode (this way, commands in subshells will terminate the script)

# Write strings to stderr
stderr() { echo -e "$@" >&2; }

# Output strings to sderr with date prefix
debug() { stderr "[$(date +%Y-%m-%d_%H-%M-%S)] $@"; }

# Write strings to stderr and exit with status code 1
die() { debug "$@" && exit 1; }

# Remove leading and trailing spaces of $1
trim() { sed -e 's/^[[:space:]]*//; s/[[:space:]]*$//' <<< "$1"; }

# Set key/values in global array from a INI-style configuration file
parse_ini_section() { local global_array=$1 file=$2 section=$3
  local section_contents
  section_contents=$(
    awk "/^\s*\[$section\]/ { flag=1; next} /^\s*\[/ { flag=0 } flag" "$file" |
    grep -v "^[[:space:]]$" | grep -v "^[[:space:]]#"
  ) || {
    debug "Cannot read section [$section] from $file"
    return 1
  }
  while IFS="=" read key value; do
    eval "$global_array[$(trim "$key")]=$(trim "$value")"
  done <<< "$section_contents"
}

# Parse arguments and populate a global array
#   $1 - Global array variable to populate
#   $2 - Coded options. Example: "output-file:|-o verbose|b no-verify"
#   $3 - Function name that prints the help message
parse_args() { local global_array=$1 coded_options=$2 print_help=$3
  local short_options long_options params value option_name short_option_name short long arg
  declare -A args_short args_long args_short_to_option_name args_value

  for option in $coded_options; do
    IFS="|" read long short <<< "$option"
    value=$([[ "${option}" =~ :$ ]] && echo "yes" || echo "no")
    option_name=${long/%:/}
    short_option_name=${short/%:/}
    args_value[$option_name]=$value
    args_long[$long]=1
    test "$short" && args_short_to_option_name[$short_option_name]=$option_name
    test "$short" && args_short[$short]=$long
  done

  short_options=$(echo "${!args_short[*]}" | tr ' ' ',')
  long_options=$(echo "${!args_long[*]}" | tr ' ' ',')
  params=$(getopt -o "h$short_options" -l "help,$long_options" --name "$0" -- "$@")
  eval set -- "$params"

  while true; do
    arg=$1
    option_name=$(sed "s/^-*//" <<< "$arg")
    if test "${arg:0:1}" == "-" && test "${arg:0:2}" != "--"; then # short option
      option_name=${args_short_to_option_name[${option_name:-_}]:-_}
    fi
    value=${args_value[${option_name:-_}]:-not_present}

    if test "$arg" == "--"; then
      break;
    elif test "$arg" == "-h" || test "$arg" == "--help"; then
      $print_help
      exit 0
    elif test "$value" == "not_present"; then
      stderr "Unknown option: $arg"
      return 1
    elif test "$value" == "yes"; then
      eval "$global_array[$option_name]=$2"
      shift 2
    elif test "$value" == "no"; then
      eval "$global_array[$option_name]=yes"
      shift 1
    else
      die "Parsing error: arg=$arg, option_name=$option_name, value=$value"
    fi
  done
}

### App

# Global variables

# ([option-name-with-value]=VALUE [option-flag]=yes)
declare -g -A args
# Current profile
declare -g profile

download() { local destdir=$1 url=$2
  local filename
  filename="$destdir/$(basename "$url")"
  debug "Download: $url"
  if wget -q -O "$filename" "$url"; then
    echo $filename
  else
    debug "Could not download: $url"
    return 1
  fi
}

start_dhis_server() { local command=$1
  debug "Start DHIS2 server: $command"
  $command
}

stop_dhis_server() { local command=$1
  debug "Stop DHIS2 server: $command"
  $command
}

run_psql() {
  sudo -u postgres psql --quiet "$@"
}

request_analytics() { local server_url=$1
  # https://docs.dhis2.org/2.26/en/developer/html/webapi_generating_resource_analytics_tables.html
  debug "Running analytics: $server_url"
  curl -sS -X POST "$server_url/api/resourceTables/analytics"
  echo
}

import_database() { local db_filename=$1 db_name=$2
  debug "Recreate database: $db_name"
  run_psql -v "ON_ERROR_STOP=1" <<< "
    -- Terminate all sessions using the database
    UPDATE pg_database SET datallowconn = 'false' WHERE datname = '$db_name';
    SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$db_name';
    -- Re-create the database
    DROP DATABASE IF EXISTS $db_name;
    CREATE DATABASE $db_name OWNER 'dhis' ENCODING 'utf8';
  "

  debug "Import DB dump: $db_filename"
  zcat -f  "$db_filename" | run_psql -v "ON_ERROR_STOP=0" "$db_name"
}

install_dhis_war() { local warfile=$1 war_destination=$2
  debug "Copy WAR: $warfile -> $war_destination"
  cp "$warfile" "$war_destination"
}

run_analytics() {
  local url=${1:-}
  if ! test "$url"; then
    die "Needs SERVER_URL"
  else
    request_analytics "$url"
  fi
}

download_from_fileurl_or_repository() { local destdir=$1 db_source=$2 hard_update=$3 profile=$4
  local protocol empty server org project blob branch path ourbranch github_dir
  debug "DB origin URL: $db_source"

  if echo "$db_source" | grep -q "^https://github.com/[^/]*/[^/]*/blob/"; then # github repo file
    IFS="/" read protocol empty server org project blob branch path <<< "$db_source"
    debug "DB origin is a github blob URL, clone repository"
    github_dir="$destdir/$org/$project"
    mkdir -p "$destdir/$org"
    if ! test -e "$github_dir"; then
      git clone "https://github.com/$org/$project" "$github_dir" >&2
    fi
    cd "$github_dir"

    # Keep different branches (dhis2-installer-PROFILE) to avoid mixing soft/hard updates
    # of profiles that use the same github URL
    git checkout -f $branch >&2
    ourbranch="dhis2-installer-$profile"
    debug "Use branch: $ourbranch"
    git branch "$ourbranch" 2>/dev/null || true
    git checkout -f "$ourbranch" >&2

    if test "$hard_update"; then
      debug "Fetch newest changes from upstream repo: $path"
      git fetch >&2
      git merge $branch >&2
      git diff-index --quiet HEAD || git commit -m "Hard update" >&2
    fi
    debug "Current commit: $(git rev-parse --verify HEAD)"
    echo "$github_dir/$path"
  else
    download "$destdir" "$db_source"
  fi
}

get_configuration_from_file() { local global_array=$1 profile=$2
  local config_path="$HOME/.dhis2-installer.conf"
  debug "Configuration file: $config_path"

  if ! test -e "$config_path"; then
    debug "Configuration file not found, use only command options"
  else
    debug "Configuration file found, get config from sections [global] and [profile:$profile]"
    parse_ini_section "$global_array" "$config_path" "global"
    parse_ini_section "$global_array" "$config_path" "profile:$profile"
  fi
}

# Show stdout and stderr to console as usual but also append to the logs file
config_logs() { local _logsdir=$1
  local timestamp logsdir
  logsdir=${_logsdir%%/}
  mkdir -p "$logsdir"
  debug "Logs directory: $logsdir"
  timestamp=$(date +%Y-%m-%d_%H-%M-%S)

  # Process substitution is not available in POSIX mode, disable it temporally
  set +o posix
  # This exec command redirects stderr/stdout to a file
  exec &> >(tee -a "$logsdir/dhis2-installer-$timestamp.log")
  # Now re-enable POSIX mode
  set -o posix
}

wait_for_server() { local url=$1 max_wait=${2:-300}
  local ts_start
  debug "Wait for server ($max_wait secs max): $url"
  ts_start=$(date +%s)

  while true; do
    if curl -s -o /dev/null --fail "$url"; then
      debug "Server is running"
      return 0
    elif test $(expr $(date +%s) - $ts_start) -ge $max_wait; then
      debug "Server could not be accessed"
      return 1
    else
      sleep 1
    fi
  done
}

set_data_directory() { local directory=$1
  local datadir=${directory%%/}
  mkdir -p "$datadir"
  debug "Data directory: $datadir"
  echo "$datadir"
}

load_args_for_update_command() { local profile_or_first_option=${1:-}
  local required_opts
  local options=(
    "soft" "hard"
    "data-directory:" "logs-directory:"
    "db-name:|n:" "db-source:"
    "start-command:" "stop-command:"
    "war-source:" "war-destination:"
    "run-analytics"
  )

  if test "${profile_or_first_option}" && test "${profile_or_first_option:0:1}" != "-"; then
    profile="$1"
    shift 1
    debug "Using profile: $profile"
    get_configuration_from_file "args" "$profile"
  fi
  parse_args "args" "${options[*]}" print_help "$@"

  # Validate arguments
  if test "${args[hard]-}"; then  # hard update
    required_opts=("db-name" "db-source" "start-command" "stop-command" "war-source" "war-destination")
  else # soft update
    required_opts=("db-name" "db-source" "start-command" "stop-command")
  fi

  for opt in ${required_opts[*]}; do
    test "${args[$opt]-}" ||  die "Required option not found: --$opt"
  done
}

update() {
  local dbfile warfile datadir

  load_args_for_update_command "$@"

  config_logs "${args[logs-directory]-./logs}"
  datadir=$(set_data_directory ${args[data-directory]-./data})

  stop_dhis_server "${args[stop-command]}"

  dbfile=$(download_from_fileurl_or_repository \
    "$datadir" "${args[db-source]}" "${args[hard]-}" "${profile:-noprofile}")
  import_database "$dbfile" "${args[db-name]}"

  if test "${args[hard]-}"; then
    warfile=$(download "$datadir" "${args[war-source]}")
    install_dhis_war "$warfile" "${args[war-destination]}"
  fi

  start_dhis_server "${args[start-command]}"

  if test "${args[run-analytics]-}"; then
    wait_for_server "${args[run-analytics]}" 300
    request_analytics "${args[run-analytics]}"
  fi

  debug "Done"
}

main() {
  local command=${1:-}
  set -o posix
  test "$#" -ge 1 && shift 1

  case "$command" in
    "-h"|"--help")
      print_help;;
    "update")
      update "$@";;
    "run-analytics")
      run_analytics "$@";;
    "")
      print_help;;
    *)
      die "Unknown command <$command>";;
  esac
}

print_help() {
  stderr """usage: dhis2-installer [-h | --help] <command> [<command_options>]

Commands:

  update [PROFILE] [OPTIONS]  Update an existing DHIS2 Tomcat instance
  run-analytics SERVER_URL    Run analytics

<update> options:

  --soft  Drop current DB and install a fresh one (keeping existing DHIS2 war) [default]
  --hard  Drop current DB, install a fresh one and update DHIS war

  --data-directory=DIRECTORY  Directory to store downloaded files and repos
  --logs-directory=DIRECTORY  Directory to store logs

  --db-name=NAME   Database name
  --db-source=URL  File URL or github blob URL (repo will be cloned)

  --start-command=NAME  Command to start the DHIS2 server
  --stop-command=NAME   Command to stop the DHIS2 server

  --war-source=URL             URL of the DHIS2 WAR to install (only on --hard)
  --war-destination=DIRECTORY  Directory to save DHIS2 war (only on --hard)

  --run-analytics=DHIS_SERVER_BASEURL   Run analytics after the update"""
}

main "$@"
