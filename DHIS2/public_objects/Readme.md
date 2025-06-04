DHIS2 Public Objects Collector

This Python script retrieves data from DHIS2 SQL Views—specifically information about public objects—and sends that data to a development instance using the Data Value API.

🚀 Purpose

The script is designed to:

Connect to one or more DHIS2 servers.

Query two SQL Views: one returning the list of public objects, the other the total count.

Send these values to a DHIS2 DEV server using tracked data elements.

🔧 Configuration

Use a JSON configuration file starting from config.json as an example


🧪 Example Usage

python3 public_objects_detector.py path/to/config.json

🛠 Features

Handles multiple source servers.

Uses token-based authentication.

Retries failed requests (configurable).

Sends:

Total number of public objects.

JSON-encoded breakdown of public objects.


📌 Notes

Ensure all tokens and access permissions are correctly configured (-r-r in the views).
The views are installed in WIDP servers.