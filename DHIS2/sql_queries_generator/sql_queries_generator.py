import argparse
import csv
import os
from os import listdir
from os.path import isfile, join

NEW_ID = "new_id"

NEW_CODE = "new_code"

OLD_ID = "old_id"

OLD_CODE = "old_code"

input = "input"
output = "queries"

update_data_value_codes_by_code_in_metadata_related = "update datavalue set value = '%s' where value like '%s' and " \
                                                      "dataelementid in (select de.dataelementid from dataelement de " \
                                                      "inner join optionset os on de.optionsetid=os.optionsetid " \
                                                      "inner join optionvalue op on op.optionsetid=os.optionsetid " \
                                                      "where op.uid like '%s');\n"
update_audit_data_values_codes_by_code_in_metadata_related = "update datavalueaudit set value = '%s' " \
                                                             "where value like '%s' and dataelementid in " \
                                                             "(select de.dataelementid from dataelement de inner join optionset os " \
                                                             "on de.optionsetid=os.optionsetid inner join optionvalue op " \
                                                             "on op.optionsetid=os.optionsetid where op.uid like '%s');\n"
update_tracked_entity_data_values_codes_by_code_in_metadata_related = "update trackedentitydatavalue set value = '%s' " \
                                                                      "where value like '%s' and dataelementid in " \
                                                                      "(select de.dataelementid from dataelement de inner join optionset os " \
                                                                      "on de.optionsetid=os.optionsetid inner join optionvalue op " \
                                                                      "on op.optionsetid=os.optionsetid where op.uid like '%s');\n"
update_audit_tracked_entity_data_values_codes_by_code_in_metadata_related = "update trackedentitydatavalueaudit " \
                                                                            "set value = '%s' where value like '%s' and dataelementid in " \
                                                                            "(select de.dataelementid from dataelement de inner join optionset os " \
                                                                            "on de.optionsetid=os.optionsetid inner join optionvalue op " \
                                                                            "on op.optionsetid=os.optionsetid where op.uid like '%s');\n"

update_data_value_codes_by_code = "update datavalue set value = '%s' where value like '%s';\n"
update_audit_data_values_codes_by_code = "update datavalueaudit set value = '%s' where value like '%s';\n"
update_tracked_entity_data_values_codes_by_code = "update trackedentitydatavalue set value = '%s' " \
                                                  "where value like '%s';\n"
update_audit_tracked_entity_data_values_codes_by_code = "update trackedentitydatavalueaudit set value = '%s' " \
                                                        "where value like '%s';\n"

show_count_of_data_values_by_code = "select count(*) from datavalue dv where dv.value like '%s';\n"
show_count_of_audit_data_values_by_code = "select count(*) from datavalueaudit dv where dv.value like '%s';\n"
show_count_of_tracked_entity_data_values_by_code = "select count(*) from trackedentitydatavalue dv where dv.value " \
                                                   "like '%s';\n"
show_count_of_audit_tracked_entity_data_values_by_code = "select count(*) from trackedentitydatavalueaudit dv where " \
                                                         "dv.value like '%s';\n"

show_data_values_by_code = "select de.uid as dataelement_uid, de.name as dataelement_name, ou.name as orgunit_name, " \
                           "ou.uid as orgunit_uid, pe.startdate, pe.enddate, coc.uid as coc_uid, coc.name as coc_name, " \
                           "value, storedby, dv.created, dv.lastupdated, dv.deleted from datavalue dv " \
                           "inner join dataelement de on de.dataelementid=dv.dataelementid " \
                           "inner join period pe on pe.periodid=dv.periodid " \
                           "inner join categoryoptioncombo coc on coc.categoryoptioncomboid=dv.categoryoptioncomboid " \
                           "inner join organisationunit ou on ou.organisationunitid=dv.sourceid where dv.value like '%s';\n"

show_audit_data_values_by_code = "select de.uid as dataelement_uid, de.name as dataelement_name, ou.name as orgunit_name, " \
                                 "ou.uid as orgunit_uid, pe.startdate, pe.enddate, coc.uid as coc_uid, coc.name as coc_name, " \
                                 "value,dv.created, dv.modifiedby, dv.audittype from datavalueaudit dv " \
                                 "inner join dataelement de on de.dataelementid=dv.dataelementid " \
                                 "inner join period pe on pe.periodid=dv.periodid " \
                                 "inner join categoryoptioncombo coc on coc.categoryoptioncomboid=dv.categoryoptioncomboid " \
                                 "inner join organisationunit ou on ou.organisationunitid=dv.organisationunitid where dv.value like '%s';\n"

show_tracked_entity_data_values_by_code = "select p.uid as program_uid, p.name as  program_name, " \
                                          "ou.uid as orgunit_uid, ou.name as orgunit_name, de.uid as dataelement_uid, de.name as dataelement_name, " \
                                          "dv.value, dv.storedby, dv.created, dv.lastupdated " \
                                          "from trackedentitydatavalue dv inner join dataelement de on de.dataelementid = dv.dataelementid " \
                                          "inner join programstageinstance psi on psi.programstageinstanceid=dv.programstageinstanceid " \
                                          "inner join programstage ps on ps.programstageid=psi.programstageid " \
                                          "inner join program p on p.programid = ps.programid inner join organisationunit ou on " \
                                          "psi.organisationunitid=ou.organisationunitid " \
                                          "where dv.value like '%s' order by p.name;\n"

show_audit_tracked_entity_data_values_by_code = "select p.uid as program_uid, p.name as  program_name, " \
                                                "ou.uid as orgunit_uid, ou.name as orgunit_name, de.uid as dataelement_uid, de.name as dataelement_name," \
                                                "dv.value, dv.modifiedby, dv.audittype " \
                                                "from trackedentitydatavalueaudit dv inner join " \
                                                "dataelement de on de.dataelementid = dv.dataelementid inner join programstageinstance psi on " \
                                                "psi.programstageinstanceid=dv.programstageinstanceid " \
                                                "inner join programstage ps on ps.programstageid=psi.programstageid " \
                                                "inner join program p on p.programid = ps.programid " \
                                                "inner join organisationunit ou on psi.organisationunitid=ou.organisationunitid " \
                                                "where dv.value like '%s' order by p.name;\n"


def assign_csv_data(row):
    if row[0] != "" and row[2] != "" and row[1] != "" and row[3] != "":
        output_data.append({OLD_CODE: row[0], OLD_ID: row[1],
                            NEW_CODE: row[2], NEW_ID: row[3]})


def main():
    global output_data
    output_data = dict()
    args = get_args()
    is_csv = lambda fname: os.path.splitext(fname)[-1] in ['.csv']
    is_not_csv = lambda fname: not os.path.splitext(fname)[-1] in ['.csv']
    is_not_git = lambda fname: not fname.startswith(".git")
    applied_filter = is_not_git if is_csv else is_not_csv

    files = [f for f in filter(applied_filter, listdir(input)) if isfile(join(input, f))]
    for path_file in files:
        output_data = list()
        with open(os.path.join("input", path_file)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    assign_csv_data(row)

                    line_count += 1
        if args.updates:
            generate_updates(path_file, args)

        if args.count:
            generate_count_values(path_file, args)

        if args.values:
            generate_show_values(path_file, args)


def generate_updates(path_file, args):
    print("Processing updates")
    with open(join(output, path_file + "_update.sql"), 'w', encoding='utf-8') as file:
        file.write('/* ~~~~~~~~~~~~~~~~~~~~~~UPDATES~~~~~~~~~~~~~~~~ */\n')
        for item in output_data:
            codes = list()
            queries = list()

            if args.datavalues:
                if args.relation:
                    queries.append(update_data_value_codes_by_code_in_metadata_related)
                else:
                    queries.append(update_data_value_codes_by_code)
            if args.datavaluesaudit:
                if args.relation:
                    queries.append(update_audit_data_values_codes_by_code_in_metadata_related)
                else:
                    queries.append(update_audit_data_values_codes_by_code)
            if args.trackedentitydatavalues:
                if args.relation:
                    queries.append(update_tracked_entity_data_values_codes_by_code_in_metadata_related)
                else:
                    queries.append(update_tracked_entity_data_values_codes_by_code)
            if args.trackedentitydatavaluesaudit:
                if args.relation:
                    queries.append(update_audit_tracked_entity_data_values_codes_by_code_in_metadata_related)
                else:
                    queries.append(update_audit_tracked_entity_data_values_codes_by_code)

            for query in queries:
                if args.relation:
                    file.write(query % (item[NEW_CODE], item[OLD_CODE], item[OLD_ID]))
                else:
                    file.write(query % (item[NEW_CODE], item[OLD_CODE]))

    print("Done")


def generate_count_values(path_file, args):
    print("Processing counts")
    with open(join(output, path_file + "_count.sql"), 'w', encoding='utf-8') as file:
        file.write('/* ~~~~~~~~~~~~~~~~~~~~~~COUNT~~~~~~~~~~~~~~~~ */\n')
        for item in output_data:
            codes = list()
            queries = list()
            if args.new:
                codes.append(NEW_CODE)
            if args.old:
                codes.append(OLD_CODE)

            if args.datavalues:
                queries.append(show_count_of_data_values_by_code)
            if args.datavaluesaudit:
                queries.append(show_count_of_audit_data_values_by_code)
            if args.trackedentitydatavalues:
                queries.append(show_count_of_tracked_entity_data_values_by_code)
            if args.trackedentitydatavaluesaudit:
                queries.append(show_count_of_audit_tracked_entity_data_values_by_code)
            for query in queries:
                for code in codes:
                    file.write(query % item[code])
    print("Done")


def generate_show_values(path_file, args):
    print("Processing Show values")
    with open(join(output, path_file + "_show_values.sql"), 'w', encoding='utf-8') as file:
        file.write('/* ~~~~~~~~~~~~~~~~~~~~~~SHOW_VALUES~~~~~~~~~~~~~~~~ */\n')
        for item in output_data:
            codes = list()
            queries = list()
            if args.new:
                codes.append(NEW_CODE)
            if args.old:
                codes.append(OLD_CODE)

            if args.datavalues:
                queries.append(show_data_values_by_code)
            if args.datavaluesaudit:
                queries.append(show_audit_data_values_by_code)
            if args.trackedentitydatavalues:
                queries.append(show_tracked_entity_data_values_by_code)
            if args.trackedentitydatavaluesaudit:
                queries.append(show_audit_tracked_entity_data_values_by_code)

            for query in queries:
                for code in codes:
                    file.write(query % item[code])
    print("Done")


def get_args():
    "Return arguments"
    parser = argparse.ArgumentParser(description=__doc__)
    print(argparse)
    add = parser.add_argument  # shortcut
    add('--ignore-show-values', dest='values', help='Ignore the show values queries',
        action='store_false')
    parser.set_defaults(values=True)
    add('--ignore-count-values', dest='count', help='Ignore the count values queries',
        action='store_false')
    parser.set_defaults(count=True)
    add('--ignore-updates', dest='updates', help='Ignore the updates queries', action='store_false')
    parser.set_defaults(updates=True)
    add('--ignore-datavalues', dest='datavalues', help='Ignore the datavalues queries'
        , action='store_false')
    parser.set_defaults(datavalues=True)
    add('--ignore-trackedentitydatavalues', help='Ignore the trackedentitydatavalues queries'
        , dest='trackedentitydatavalues', action='store_false')
    parser.set_defaults(trackedentitydatavalues=True)
    add('--ignore-datavaluesaudit', dest='datavaluesaudit', help='Ignore the datavaluesaudit queries'
        , action='store_false')
    parser.set_defaults(datavaluesaudit=True)
    add('--ignore-trackedentitydatavaluesaudit', help='Ignore the trackedentitydatavaluesaudit queries',
        dest='trackedentitydatavaluesaudit', action='store_false')
    parser.set_defaults(trackedentitydatavaluesaudit=True)
    add('--ignore-new-codes', dest='new', help='Ignore the new code queries',
        action='store_false')
    parser.set_defaults(new=True)
    add('--ignore-old-codes', dest='old', help='Ignore the old code queries', action='store_false')
    add('--ignore-relation-check', dest='relation', help='Ignore the relation check', action='store_false')
    parser.set_defaults(relation=True)
    return parser.parse_args()


if __name__ == '__main__':
    main()
