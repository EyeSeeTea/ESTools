import re

start = 100
end = 232

with open("unified_logs.log", "w", encoding='utf-8') as out_file:
    for i in range(start, end + 1):
        try:
            with open(f"logs/dhis-audit.log.{i}", "r", encoding='utf-8') as log_file:
                for line in log_file:
                    processed_line = re.sub(r' \(AbstractAuditConsumer.*', '', line)
                    out_file.write(processed_line)
        except FileNotFoundError:
            print(f"File dhis-audit.log.{i} not found")

print("Success.")