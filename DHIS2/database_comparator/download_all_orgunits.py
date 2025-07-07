import requests
import json
from requests.auth import HTTPBasicAuth

# Base URL of the DHIS2 instance
BASE_URL = "https://play/dhis2"
OUTPUT_FILE="organisation_units.json"
USERNAME = ""
PASSWORD = ""
PAGE_SIZE = 5000
# Pagination parameters
FIELDS = "name,code,shortName,created,path,level,geometry,id,children::size"

# If using cookie authentication, provide the cookie here
COOKIE = "JSESSIONID=;"

# Common headers for both authentication methods
HEADERS = {
    "Accept": "application/json"
}
if COOKIE:
    HEADERS["Cookie"] = COOKIE


# Container to hold all organisation units
all_org_units = []

# Pagination control
page = 1
has_more = True

while has_more:
    print(f"Downloading page {page}...")
    url = f"{BASE_URL}/api/organisationUnits"
    params = {
        "fields": FIELDS,
        "pageSize": PAGE_SIZE,
        "page": page
    }

    # Perform the request with the selected authentication method
    if COOKIE:
        response = requests.get(url, params=params, headers=HEADERS)
    else:
        response = requests.get(url, params=params, headers=HEADERS, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    # Handle unauthorized access
    if response.status_code == 401:
        raise Exception("Unauthorized access. Check your credentials or cookie.")
    response.raise_for_status()
    data = response.json()

    # Get the list of organisation units
    org_units = data.get("organisationUnits", [])

    # Remove geometry["coordinates"] if it exists
    for unit in org_units:
        geometry = unit.get("geometry")
        if isinstance(geometry, dict) and "coordinates" in geometry:
            del geometry["coordinates"]

    # Append to the result list and control pagination
    if not org_units:
        has_more = False
    else:
        all_org_units.extend(org_units)
        page += 1

print(f"Total downloaded organisation units: {len(all_org_units)}")

# Save all organisation units to a JSON file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"organisationUnits": all_org_units}, f, indent=2, ensure_ascii=False)