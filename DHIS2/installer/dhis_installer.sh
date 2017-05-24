#!/bin/bash
set -e -u -o pipefail 

# Bash set options:
#   -e          -- Exit when any command fails
#   -u          -- Exit when the script uses an undefined variable
#   -o pipefail -- Exit when a command in a pipe fails
#   -o posix    -- Enable Posix mode (amongst other things, commands in subshells inherit set -e)

### Generic functions

# Write strings to stderr
stderr() { echo -e "$@" >&2; }

# Write strings to stderr and exit
die() { debug "$@" && exit 1; }

# Remove leading and trailing spaces of variable
trim() { sed -e 's/^[[:space:]]*//; s/[[:space:]]*$//' <<< "$1"; }

# Set key/values in <global_array> from a INI-style configuration file
parse_ini_section() { local global_array=$1 file=$2 section=$3
  local section_contents
  section_contents=$(
    awk "/^\s*\[$section\]/ { flag=1; next} /^\s*\[/ { flag=0 } flag" "$file" | 
    grep -v "^[[:space:]]$"
  ) || {
    debug "Cannot read section [$section] from $file"
    return 1
  }
  while IFS="=" read key value; do
    eval "$global_array[$(trim "$key")]=$(trim "$value")"
  done <<< "$section_contents"
}

# Parse arguments populating args/args_value
parse_args() { local global_array=$1 coded_options=$1 print_help=$2
  local options long_options params value option_name short_option_name short long arg
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

  long_options=$(echo "${!args_long[*]}" | tr ' ' ',')
  params=$(getopt -o "h${!args_short[*]}" -l "help,$long_options" --name "$0" -- "$@")
  eval set -- "$params"

  while true; do
    arg=$1
    option_name=$(sed "s/^-*//" <<< "$arg")
    if test "${arg:0:1}" == "-" -a "${arg:0:2}" != "--"; then # short option
      option_name=${args_short_to_option_name[${option_name:-_}]:-_}
    fi
    value=${args_value[${option_name:-_}]:-not_present}

    if test "$arg" == "--"; then
      break;
    elif test "$arg" == "-h" -o "$arg" == "--help"; then
      $print_help
      exit 2
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
#
# args : ([option-name-with-value]=VALUE [option-flag]=yes)
declare -g -A args 

# logfile : File to store logs
logfile=

debug() { 
  local with_prefix
  with_prefix="[$(date +%Y-%m-%d_%H-%M-%S)] $@"
  stderr "$with_prefix"
}

download() { local destdir=$1 url=$2
  local filename
  filename="$destdir/$(basename "$url")"
  debug "Download: $url"
  wget -q -O "$filename" "$url"
  echo $filename
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
  sudo -u postgres psql --quiet
}

request_analytics() { local server_url=$1
  # https://docs.dhis2.org/2.26/en/developer/html/webapi_generating_resource_analytics_tables.html
  debug "Running analytics: $server_url"
  curl -u "admin:district" -X POST "$server_url/api/resourceTables/analytics"
  echo 
}

import_database() { local db_filename=$1 db_name=$2
  debug "Recreate database: $db_name"
  run_psql <<< "
    DROP DATABASE IF EXISTS $db_name;
    CREATE DATABASE $db_name OWNER 'dhis' ENCODING 'utf8';
  "
  debug "Import DB dump: $db_filename"
  zcat -f  "$db_filename" | run_psql "$db_name"
}

install_dhis_war() { local warfile=$1 war_destination=$2
  debug "Copy WAR: $warfile -> $war_destination"
  cp "$warfile" "$war_destination"
} 

validate_args_for_update_command() {
  local required_opts
  if test "${args[hard-update]-}"; then  # hard update
    required_opts=("db-name" "db-source" "start-command" "stop-command" "war-source" "war-destination")
  else # soft update
    required_opts=("db-name" "db-source" "start-command" "stop-command")
  fi

  for opt in ${required_opts[*]}; do
    if test -z "${args[$opt]-}"; then
      die "Required option not found: --$opt"
    fi
  done
}

run_analytics() {
  parse_args "args" "server-url:|-s:" print_help "$@"
  test -z "${args[server-url]-}" && die "Required option not found: --server-url"
  request_analytics "${args[server-url]}"
}

download_from_fileurl_or_repository() { local destdir=$1 db_source=$2 perform_pull=$3
  local protocol empty server org project blob branch path
  debug "DB origin URL: $db_source"

  if echo "$db_source" | grep -q "^https://github.com/[^/]*/[^/]*/blob/"; then # github repo file
    IFS="/" read protocol empty server org project blob branch path <<< "$db_source"
    debug "DB origin is a github blob URL, clone repository"
    git clone "https://github.com/$org/$project" "$destdir/$project"
    (
      cd "$destdir/$project"
      debug "Use branch: $branch"
      git checkout $branch
      if test "$perform_pull"; then
        debug "Hard update: pull changes from repo"
        git pull
      else
        debug "Soft update: don't pull changes from repo"
      fi
    )
    echo "$destdir/$project/$path"
  else
    download "$destdir" "$db_source"
  fi
}

get_configuration_from_file() { local global_array=$1 profile=$2
  local config_path="$HOME/.dhis-installer.rc"
  debug "Check configuration file: $config_path"

  if ! test -e "$config_path"; then
    debug "Configuration file not found, use only options"
    return
  else
    debug "Configuration file found, get config from sections [global] and [profile:$profile]"
    parse_ini_section "$global_array" "$config_path" "global"
    parse_ini_section "$global_array" "$config_path" "profile:$profile"
  fi
}

config_logs() { local _logsdir=$1
  logsdir=${_logsdir%%/}
  mkdir -p "$logsdir"
  debug "Logs directory: $logsdir"
  # Process substitution is not avaiable for POSIX mode, disable it temporally
  #set +o posix
  local timestamp=$(date +%Y-%m-%d_%H-%M-%S)
  exec &> >(tee -a "$logsdir/$timestamp.log")
  #set -o posix
}

update() {
  local dbfile warfile datadir
  local options=(
    "soft" "hard"
    "data-directory:" "logs-directory:"
    "db-name:|n:" "db-source:"
    "start-command:" "stop-command:"
    "war-source:" "war-destination:"
    "run-analytics"
  )

  if test "${1:0:1}" != "-"; then 
    # first argument is not an option, assume it's the profile name
    get_configuration_from_file "args" "$1"
    shift 1
  fi
  echo "$@"
  parse_args "args" "${options[*]}" print_help "$@"
  validate_args_for_update_command

  config_logs "${args[logs-directory]-./logs}"

  set -o posix

  local _datadir=${args[data-directory]-./data}
  local datadir=${_datadir%%/}
  mkdir -p "$datadir"
  debug "Data directory: $datadir"

  stop_dhis_server "${args[stop-command]}"
  dbfile=$(download_from_fileurl_or_repository "$datadir" "${args[db-source]}" "${args[hard]-1}")
  if test "${args[hard-update]-}"; then
    warfile=$(download "$datadir" "${args[war-source]}")
    install_dhis_war "$warfile" "${args[war-destination]}"
  fi
  import_database "$dbfile" "${args[db-name]}"
  start_dhis_server "${args[start-command]}"
  if test "${args[run-analytics]-}"; then
    request_analytics "${args[run-analytics]}"
  fi
}

main() {
  local command=${1:-}
  test "$#" -ge 1 && shift 1

  case "$command" in
    "update")
      update "$@";;
    "run-analytics")
      run_analytics "$@";;
    "")
      print_help;;
    *)
      stderr "Unknown command <$command>"
      exit 2;;
  esac
}

print_help() {
  tabs 2
  stderr "usage: dhis_installer [-h] <command> [<command_options>]"
  stderr
  stderr "Commands:"
  stderr
  stderr "\t" "update [PROFILE]" "\t\t" "Drop current DB and install a fresh one"
  stderr "\t" "run-analytics" "\t\t" "Drop current DB and install a fresh one"
  stderr "\t" "-h | --help" "\t\t" "Show this help message"
  stderr
  stderr "Use PROFILE from a profile:PROFILE INI section read from ~/.dhis_installer.rc"
  stderr
  stderr "<update> options:"
  stderr
  stderr "\t" "--soft" "\t\t" "Drop current DB and install a fresh one (keep DHIS2 war) [default]"
  stderr "\t" "--hard" "\t\t" "Drop current DB and install a fresh one and update DHIS war"
  stderr "\t" "--data-directory" "\t\t" "Base directory to store logs and cached data"
  stderr "\t" "--db-name=NAME" "\t" "Database name"
  stderr "\t" "--start-command=NAME" "\t" "Command to start DHIS2 server"
  stderr "\t" "--stop-command=NAME" "\t" "Command to stop DHIS2 server"
  stderr "\t" "--war-source=URL" "\t" "URL of the DHIS2 WAR to install"
  stderr "\t" "--war-destination=DIRECTORY" "\t" "Directory to save DHIS2 war"
  stderr "\t" "--run-analytics=DHIS_SERVER_BASEURL" "\t" "Run Analytics in this DHIS2 server"
  stderr "\t" "--data-directory=DIRECTORY" "\t" "Directory to store downloaded files and repos"
  stderr "\t" "--logs-directory=DIRECTORY" "\t" "Directory to store logs"
  stderr
  stderr "<run-analytics> options:"
  stderr
  stderr "\t" "-s|--server-url=BASEURL" "URL to DHIS2 server"
}

main "$@"