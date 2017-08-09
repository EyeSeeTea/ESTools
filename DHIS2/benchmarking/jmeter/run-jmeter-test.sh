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

run_for_users() { local name=$1 users_list=$2 test_plan_file=$3 properties=$4
  local results_file
  for users in $(echo $users_list | splitcommas); do
    debug "Run for users: $users"
    results_file="$(dirname "$test_plan_file")/${name}-users${users}.jtl"
    rm -f "$results_file"
    run_jmeter_test_plan "$test_plan_file" "$results_file" "$properties,users=$users"
    python group-jmeter-results-by-controller.py "$results_file"
  done
}

main() {
  if test $# -lt 4; then
    debug "Usage $(basename "$0") NAME NUSER1[,NUSER2,...] INPUT_TEST_PLAN_JMX_PATH PROP1=VALUE1,PROP2=VALUE2...]"
    exit 1
  else
    run_for_users "$@"
  fi
}

main "$@"