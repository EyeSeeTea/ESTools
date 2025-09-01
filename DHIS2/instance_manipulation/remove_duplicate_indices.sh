DB=""
user=""
pass=""
host=""
port=5432
echo "SELECT (array_agg(idx))[2] AS index
FROM (
    SELECT indexrelid::regclass AS idx, (indrelid::text ||E'\n'|| indclass::text ||E'\n'|| indkey::text ||E'\n'||
                                         COALESCE(indexprs::text,'')||E'\n' || COALESCE(indpred::text,'')) AS KEY
    FROM pg_index) sub
GROUP BY KEY HAVING COUNT(*)>1
ORDER BY SUM(pg_relation_size(idx)) DESC;
" | psql -d postgresql://${user}:${pass}@${host}:${port}/"${DB}" -A | tail -n+2 | head -n-1 | while read IDX
do
    SQL="DROP INDEX CONCURRENTLY ${IDX}"
    echo "${SQL}"
    echo "${SQL}" | psql -d postgresql://${user}:${pass}@${host}:${port}/"${DB}"
done