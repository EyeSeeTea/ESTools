#!/bin/bash

# Written by demofly for Pg 9.4
# Adapted by EyeSeeTea Ltd for Pg 10
#
# WARNING: if you ran pg_stat_reset() last month, don't use this script !!!
#
# Get unused indexes and kill it with fire!

DB=db
user=user
pass=pass
host=localhost
port=5432

echo "select
    indexrelid::regclass as index
from
    pg_stat_user_indexes
    JOIN pg_index USING (indexrelid)
where
    idx_scan = 0 and indisunique is false;
" | psql -d postgresql://${user}:${pass}@${host}:${port}/"${DB}" -A | tail -n+2 | head -n-1 | while read IDX
do
    SQL="DROP INDEX CONCURRENTLY ${IDX}"
    echo "${SQL}"
    echo "${SQL}" | psql -d postgresql://${user}:${pass}@${host}:${port}/"${DB}"
done
