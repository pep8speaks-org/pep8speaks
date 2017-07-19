import os
import requests
from pep8speaks.constants import AUTH


def _request(query=None, type='GET', json={}, data=''):
    args = (query)
    kwargs = {'auth': AUTH}
    if json: kwargs['json'] = json
    if data: kwargs['data'] = data

    if type == 'GET':
        return requests.get(*args, **kwargs)
    elif type == 'POST':
        return requests.post(*args, **kwargs)
    elif type == 'PUT':
        return requests.put(*args, **kwargs)
