import requests


class Dhis2Api:
    """
    Dhis2 API wrapper.

        >> api = Dhis2Api('http://localhost:8080/', username='admin',
                          password='district')
        >> api.get('/users')
        >> api.get('/users/1', {'fields': 'id, displayName, created'})
        >> api.post('/users/1', ...)
        >> api.put('/users/2', ...)
        >> api.patch('/users/3', ...)
    """
    def __init__(self, url, username='admin', password='district'):
        self.api_url = url.rstrip('/') + '/api'
        self.auth = requests.auth.HTTPBasicAuth(username, password)

    def _request(self, method, path, **kwargs):
        url = self.api_url + path
        request_method = getattr(requests, method)
        response = request_method(url, auth=self.auth, **kwargs)
        response.raise_for_status()
        if response.text:
            return response.json()
        else:
            return response

    def get(self, path, params=None):
        return self._request('get', path, params=params)

    def post(self, path, payload):
        return self._request('post', path, json=payload)

    def put(self, path, payload):
        return self._request('put', path, json=payload)

    def patch(self, path, payload):
        return self._request('patch', path, json=payload)

    def delete(self, path):
        return self._request('delete', path)
