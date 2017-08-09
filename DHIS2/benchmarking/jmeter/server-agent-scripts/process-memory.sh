#!/bin/bash
set -e -u
instance_name=$1
pgrep -f "[/]instances/$instance_name/" | xargs -ri ps -o "rss" --pid {} --no-headers | xargs numfmt --from-unit=1024 --to-unit=M
