import re
import json

# Ask the user to enter a date for filtering
fecha = input("Please enter a date in the format YYYY-MM-DD: ")

# Validate that the entered date has the correct format
if fecha != "":
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha):
        print("Invalid date. Please enter a date in the format YYYY-MM-DD.")
        exit()

# Ask the user to enter an auditScope type (optional)
audit_scope = input("Enter the auditScope type (optional, press Enter to skip): ")

# Ask the user to enter a value for klass (optional)
klass_prefix = input("Enter the initial value for 'klass' (optional, press Enter to skip): ")

# Ask the user to enter the name of the 'createdBy' user
created_by = input("Enter the name of the 'createdBy' user (optional, press Enter to skip): ")

# Open and read the unified log file
try:
    with open("unified_logs.log", "r", encoding="utf-8") as infile, open(f"filtered_logs_{fecha}_{audit_scope if audit_scope else 'ALL'}_{klass_prefix if klass_prefix else 'ALL'}_{created_by if created_by else 'ALL'}.json", "w", encoding="utf-8") as outfile:

        outfile.write('{"audit":[')
        first_line_written = False
        # Iterate over each line in the unified log file
        for line in infile:
            # Check if the line contains the entered date
            if line.startswith(f"* INFO  {fecha}"):
                # Extract the JSON part of the line
                json_part = re.search(r'{.*}', line)
                if json_part:
                    json_data = json.loads(json_part.group())
                    # Check if the line matches all entered criteria
                    if (not audit_scope or json_data.get('auditScope') == audit_scope.upper()) and \
                       (not klass_prefix or json_data.get('klass', '').startswith(klass_prefix)) and \
                       (not fecha or json_data.get('createdAt', '').startswith(fecha)) and \
                       (not created_by or json_data.get('createdBy') == created_by):
                        processed_line = ('' if not first_line_written else ',') + re.sub(r'^[^{]+', '', line).rstrip()
                        # Write the processed line to the output file
                        outfile.write(processed_line)
                        first_line_written = True  # Update control variable

        # Finalize JSON array
        outfile.write(']}')

    # Inform the user that the process is complete
    print(f"Lines with date {fecha}{' and auditScope ' + audit_scope if audit_scope else ''}{' and klass starting with ' + klass_prefix if klass_prefix else ''}{' and createdBy ' + created_by if created_by else ''} have been filtered and saved to filtered_logs_{fecha}_{audit_scope if audit_scope else 'ALL'}_{klass_prefix if klass_prefix else 'ALL'}_{created_by if created_by else 'ALL'}.json")

except FileNotFoundError:
    print("File unified_logs.log not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
