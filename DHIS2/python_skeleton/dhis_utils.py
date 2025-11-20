# dhis_utils.py

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
