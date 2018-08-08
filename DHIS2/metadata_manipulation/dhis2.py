"""
Make dhis2 GET and POST actions.

After importing the module and before using the functions, one must initialize
the URLBASE and USER variables.
"""

from random import choice
import requests
import json
import functools

URLBASE = None
USER = None

gen_chars = lambda c, n: ''.join(chr(i) for i in range(ord(c), ord(c) + n))
AZaz = gen_chars('A', 26) + gen_chars('a', 26)  # 'A..Za..z'
AZaz09 = AZaz + gen_chars('0', 10)  # 'A..Za..z0..9'


def get(query):
    check_initialization()
    url = URLBASE + "/api/" + query
    auth = requests.auth.HTTPBasicAuth(*USER.split(':', 1))
    response = requests.get(url, auth=auth)
    return json.loads(response.text)


def post(command, payload):
    check_initialization()
    url = URLBASE + "/api/" + command
    auth = requests.auth.HTTPBasicAuth(*USER.split(':', 1))
    response = requests.post(url, json=payload, auth=auth)
    return json.loads(response.text)


def put(endpoint, payload):
    check_initialization()
    url = URLBASE + "/api/" + endpoint
    auth = requests.auth.HTTPBasicAuth(*USER.split(':', 1))
    response = requests.put(url, json=payload, auth=auth)
    return json.loads(response.text)


def delete(endpoint):
    check_initialization()
    url = URLBASE + "/api/" + endpoint
    auth = requests.auth.HTTPBasicAuth(*USER.split(':', 1))
    response = requests.delete(url, auth=auth)
    return json.loads(response.text)


def check_initialization():
    assert USER is not None and ':' in USER, "Must specify user (username:pass)"
    assert URLBASE is not None, "Must specify base url"


def generate_uid():
    "Return a uid that can be used for dhis2"
    # From the doc on "Generate identifieres" at
    # https://docs.dhis2.org/2.28/en/developer/html/webapi_system_resource.html
    # they need to be 11 A-Za-z0-9 characters long, starting with A-Za-z only.
    return choice(AZaz) + ''.join(choice(AZaz09) for i in range(10))


# From https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
def memoize(f):
    "Decorator to remember the outputs for already given inputs"
    cache = f.cache = {}
    @functools.wraps(f)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]
    return memoizer


@memoize
def get_object(oid):
    try:
        href = get('identifiableObjects/%s' % oid)['href']
        url = '/'.join(href.rsplit('/', 2)[-2:])
        return get(url)
    except KeyError:
        raise RuntimeError('Cannot get information from object id %s' % oid)
