import collections
import fnmatch
import hmac
import json
import os

from flask import abort
from flask import Response as FResponse
import requests
from requests.packages.urllib3.util.retry import Retry
from pep8speaks.constants import AUTH, GH_API


def query_request(query=None, method="GET", **kwargs):
    """
    Queries like /repos/:id needs to be appended to the base URL,
    Queries like https://raw.githubusercontent.com need not.

    full list of kwargs see http://docs.python-requests.org/en/master/api/#requests.request
    """

    if query[0] == "/":
        query = 'https://' + GH_API + query

    request_kwargs = {
        "auth": AUTH,
        "timeout": 8,
    }
    request_kwargs.update(**kwargs)

    s = requests.Session()
    retries = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1.0,
        method_whitelist=frozenset(['GET', 'POST']),
        status_forcelist=(500, 502, 503, 504, 409, 422),
    )
    s.mount("http://", requests.adapters.HTTPAdapter(max_retries=retries))
    s.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))

    return s.request(method, query, **request_kwargs)



def Response(data=None, status=200, mimetype='application/json'):
    if data is None:
        data = {}

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
        if ('X-Hub-Signature' in request.headers and
           request.headers.get('X-Hub-Signature') is not None):
            header_signature = request.headers.get('X-Hub-Signature', None)
        else:
            abort(403)
        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            abort(501)

        mac = hmac.new(os.environ["GITHUB_PAYLOAD_SECRET"].encode(),
                       msg=request.data,
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
