## Queries generator script

The script can:

- Generate queries for datavalues.
- Generate queries for datavalueaudit.
- Generate queries for trackedentitydatavalue.
- Generate queries for trackedentitydatavalueaudit.

#Type of queries in separated files
- Update of value (name of input file +_update.sql).
- Count of values (name of input file +_count.sql).
- Select of values with human readable output (name of input file +_show_values.sql).

#Ignore queries flags as params
  --ignore-show-values  Ignore the show values queries
  --ignore-count-values 
                        Ignore the count values queries
  --ignore-updates      Ignore the updates queries
  --ignore-datavalues   Ignore the datavalues queries
  --ignore-trackedentitydatavalues
                        Ignore the trackedentitydatavalues queries
  --ignore-datavaluesaudit
                        Ignore the datavaluesaudit queries
  --ignore-trackedentitydatavaluesaudit
                        Ignore the trackedentitydatavaluesaudit queries
  --ignore-new-codes    Ignore the new code queries
  --ignore-old-codes    Ignore the old code queries
  --ignore-relation-check Ignore the relation in the old metadata 
  to generate the update queries (for example: 
  ignore the dataelement relation of a dataelement 
  with the optionset parent of the old option in the datavalues)



#Supported metadata
- Only options for now.

#Input requirements
A csv file with the old_code;old_id;new_code;new_id for each line with a header (the first line will be ignored)
