#!/bin/bash
#
# Run JMeter test plan with custom properties and save the JTL results files
#
set -e -u -o pipefail

debug() { echo "$@" >&2; }

splitcommas() { tr ',' '\n'; }

run_jmeter_test_plan() { local test_plan_file=$1 results_file=$2 properties=$3
  local cmd_properties
  cmd_properties=$(for prop_value in $(echo $properties | splitcommas); do echo "-J $prop_value"; done | xargs)
  debug "Input JMX test plan: $test_plan_file"
  debug "Output JTL results: $results_file"
  debug "Properties: $cmd_properties"
  jmeter -n -t "$test_plan_file" -l "$results_file" $cmd_properties
}

run_for_users() { local test_plan_file=$1 instances=$2 users_list=$3 properties=$4 output_dir=$5
  local results_file name directory results_files path_prefix
  directory="$output_dir/$(dirname "$test_plan_file")/$(basename "$test_plan_file" ".jmx")"
  debug "Output directory: $directory"
  mkdir -p "$directory"

  for instance in $(echo $instances | splitcommas); do
    results_files=""
    for users in $(echo $users_list | splitcommas); do
      debug "Run: instance=$instance, users=$users"
      name="${instance}-users${users}"
      results_file="${directory}/${name}.jtl"
      rm -f "$results_file" "$name-perfmon.jtl"
      path_prefix="/${instance}"
      run_jmeter_test_plan "$test_plan_file" "$results_file" \
        "$properties,path_prefix=$path_prefix,name=$name,users=$users"
      sh /opt/jmeter/bin/JMeterPluginsCMD.sh --generate-png ${directory}/${name}-perfmon.png \
        --input-jtl ${name}-perfmon.jtl --plugin-type PerfMon --width 800 --height 600 --granulation 30000
      results_files="$results_files $results_file"
    done

    ./group-jmeter-results-by-controller.py "${directory}/${instance}-elapsed.png" $results_files
  done
}

main() {
  if test $# -lt 5; then
    debug "Usage $(basename "$0")"
    debug "   INPUT_TEST_PLAN_JMX_PATH"
    debug "   [INSTANCE1,INSTANCE2...]"
    debug "   NUSER1[,NUSER2,...]"
    debug "   PROP1=VALUE1,PROP2=VALUE2...]"
    debug "   OUTPUT_DIRECTORY"
    exit 1
  else
    run_for_users "$@"
  fi
}

main "$@"