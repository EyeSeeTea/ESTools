import re
import sys

def extract_and_write_queries(temp_log_file, sql_output_file, user_to_takeover):
    with open(temp_log_file, 'r') as infile, open(sql_output_file, 'a') as outfile:
        lines = infile.readlines()
        for i in range(1, len(lines)):
            line = lines[i]
            if "Status code: 500" in line:
                match = re.search(r"ID (\S+)\. Status code: 500", line)
                if match:
                    some_id = match.group(1)
                    query1 = f"select userinfoid from userinfo where uid='{some_id}'\n"

                    # Read the previous line
                    previous_line = lines[i - 1]
                    constraint_match = re.search(r'ERROR:  update or delete on table "userinfo" violates foreign key constraint "(\S+)" on table "(\S+)"', previous_line)
                    if constraint_match:
                        query_user = f"select userinfoid from userinfo where username='{user_to_takeover}'\n"
                        some_constraint = constraint_match.group(1)
                        some_table = constraint_match.group(2)
                        if "lastupdateby" in some_constraint.lower():
                            query2 = f"update {some_table} set lastupdatedby=({query_user.strip()}) where lastupdatedby=({query1.strip()});\n"
                        elif "lastupdatedby" in some_constraint.lower():
                            query2 = f"update {some_table} set lastupdatedby=({query_user.strip()}) where lastupdatedby=({query1.strip()});\n"
                        elif "creator" in some_constraint.lower():
                            query2 = f"update {some_table} set creator=({query_user.strip()}) where creator=({query1.strip()});\n"
                        elif "assigneduserid" in some_constraint.lower():
                            query2 = f"update {some_table} set assigneduserid=({query_user.strip()}) where assigneduserid=({query1.strip()});\n"
                        else:
                            query2 = f"update {some_table} set userid=({query_user.strip()}) where userid=({query1.strip()});\n"

                        lines_present = set()
                        for l in temp_log_file:
                            if l not in lines_present:
                                outfile.write(query2)
                                lines_present.add(l)

if __name__ == "__main__":
    
    temp_log_file = sys.argv[1]
    sql_output_file = sys.argv[2]
    user_to_takeover = sys.argv[3]
    
    extract_and_write_queries(temp_log_file, sql_output_file, user_to_takeover)
