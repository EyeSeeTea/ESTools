#!/bin/bash
set -e -u -o pipefail

stderr() { echo -e "$@" >&2; }

debug() { stderr "[$HOSTNAME $(date +%Y-%m-%d_%H-%M-%S)] $@"; }

repo_url=$1 repo_destination=$2 repo_branch=$3 repo_path=$4 import_dir=$5
debug "Getting $repo_url -> $repo_destination  url  -> $repo_url branch -> $repo_branch path -> $repo_path import -> $import_dir"
if test -d "$repo_destination"; then
  debug "The repository exists, pull latest changes"
  cd "$repo_destination"
  git checkout $repo_branch && git fetch && git reset --hard origin/$repo_branch
else
  debug "Cloning repository"
  debug "git clone -b $repo_branch $repo_url $repo_destination"
  git clone -b "$repo_branch" "$repo_url" "$repo_destination"
fi
pwd
cp $repo_path/. $import_dir -r