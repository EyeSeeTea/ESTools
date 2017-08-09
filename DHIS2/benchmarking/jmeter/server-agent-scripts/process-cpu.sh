#!/bin/bash
set -e -u
echo "$@" >> /tmp/log
instance_name=$1
pgrep -f "[/]instances/$instance_name/" | xargs -ri pidstat -h -r -u -v -p {} 1 1 | grep -P "^\s*\d" | awk '{print $7}'
