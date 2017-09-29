import collections
import fnmatch
import hmac
import json
import os

from flask import abort
from flask import Response as FResponse
import requests
from pep8speaks.constants import AUTH, BASE_URL


def _request(query=None, type='GET', json={}, data='', headers=None, params=None):
    query = BASE_URL + query
    args = (query,)
    kwargs = {'auth': AUTH}
    if json: kwargs['json'] = json
    if data: kwargs['data'] = data
    if headers: kwargs['headers'] = headers
    if params: kwargs['params'] = params

    if type == 'GET':
        return requests.get(*args, **kwargs)
    elif type == 'POST':
        return requests.post(*args, **kwargs)
    elif type == 'PUT':
        return requests.put(*args, **kwargs)
    elif type == 'PATCH':
        return requests.patch(*args, **kwargs)
    elif type == 'DELETE':
        return requests.delete(*args, **kwargs)


def Response(data={}, status=200, mimetype='application/json'):
    response_object = json.dumps(data, default=lambda obj: obj.__dict__)
    return FResponse(response_object, status=status, mimetype=mimetype)


def update_dict(base, head):
    """
    Recursively merge or update dict-like objects.
    >>> update({'k1': 1}, {'k1': {'k2': {'k3': 3}}})

    Source : http://stackoverflow.com/a/32357112/4698026
    """
    for key, value in head.items():
        if key in base:
            if isinstance(base, collections.Mapping):
                if isinstance(value, collections.Mapping):
                    base[key] = update_dict(base.get(key, {}), value)
                else:
                    base[key] = head[key]
            else:
                base = {key: head[key]}
    return base


def match_webhook_secret(request):
    """Match the webhook secret sent from GitHub"""
    if os.environ.get("OVER_HEROKU", False):
        header_signature = request.headers.get('X-Hub-Signature')
        if header_signature is None:
            abort(403)
        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            abort(501)
        mac = hmac.new(os.environ["GITHUB_PAYLOAD_SECRET"].encode(), msg=request.data,
                       digestmod="sha1")
        if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
            abort(403)
    return True


def filename_match(filename, patterns):
    """
    Check if patterns contains a pattern that matches filename.
    """

    # `dir/*` works but `dir/` does not
    for index in range(len(patterns)):
        if patterns[index][-1] == '/':
            patterns[index] += '*'

    # filename has a leading `/` which confuses fnmatch
    filename = filename.lstrip('/')

    # Pattern is a fnmatch compatible regex
    if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns):
        return True

    # Pattern is a simple name of file or directory (not caught by fnmatch)
    for pattern in patterns:
        if '/' not in pattern and pattern in filename.split('/'):
            return True

    return False
