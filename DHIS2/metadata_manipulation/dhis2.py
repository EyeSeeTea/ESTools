"""
Make dhis2 GET and POST actions.

After importing the module and before using the functions, one must initialize
the URLBASE and USER variables.
"""

import requests
import json

URLBASE = None
USER = None


def get(query):
    assert USER is not None and ':' in USER, "Must specify user"
    assert URLBASE is not None, "Must specify base url"
    user, passwd = USER.split(':', 1)
    url = URLBASE + "/api/" + query
    response = requests.get(url, auth=requests.auth.HTTPBasicAuth(user, passwd))
    return json.loads(response.text)


def post(command, payload):
    assert USER is not None and ':' in USER, "Must specify user"
    assert URLBASE is not None, "Must specify base url"
    user, passwd = USER.split(':', 1)
    url = URLBASE + "/api/" + command
    response = requests.post(url, json=payload,
                             auth=requests.auth.HTTPBasicAuth(user, passwd))
    return json.loads(response.text)
