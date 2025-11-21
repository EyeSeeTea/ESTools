# dhis_utils.py

import sys
import requests


def dhis_get(
    path: str,
    base_url: str,
    jsessionid: str,
    params: dict | None = None,
    timeout: int = 30,
) -> dict:
    """
    Perform a GET request to a DHIS2 instance using a JSESSIONID cookie.

    Args:
        path: API path, e.g. "/api/system/info".
        base_url: Base URL of the DHIS2 instance, e.g. "https://my-dhis2".
        jsessionid: Value of the JSESSIONID cookie.
        params: Optional query parameters.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response as a Python dict.

    Raises:
        requests.HTTPError if the response status is not 2xx.
    """
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    cookies = {"JSESSIONID": jsessionid}
    response = requests.get(url, params=params or {}, cookies=cookies, timeout=timeout)
    response.raise_for_status()
    return response.json()


def test_connection(
    base_url: str,
    jsessionid: str,
    timeout: int = 10,
) -> dict:
    """
    Test connection against /api/system/info.
    If it fails, print an error and abort the script.

    Returns:
        system/info JSON dict if everything is OK.

    Exits:
        Calls sys.exit(1) on any error.
    """
    try:
        system_info = dhis_get(
            path="/api/system/info",
            base_url=base_url,
            jsessionid=jsessionid,
            params=None,
            timeout=timeout,
        )
    except requests.HTTPError as http_error:
        status = http_error.response.status_code if http_error.response is not None else "?"
        print(f"[FATAL] HTTP error {status} while calling /api/system/info at {base_url}")
        sys.exit(1)
    except requests.RequestException as req_error:
        print(f"[FATAL] Could not connect to {base_url} (/api/system/info): {req_error}")
        sys.exit(1)
    except Exception as unexpected:
        print(f"[FATAL] Unexpected error while testing connection to {base_url}: {unexpected}")
        sys.exit(1)

    print(
        f"[OK] Connected to DHIS2 at {base_url} "
        f"(version={system_info.get('version', 'unknown')})"
    )
    return system_info
