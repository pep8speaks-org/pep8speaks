import hmac
import os
import pytest
import werkzeug
import mock
from pep8speaks.utils import update_dict, match_webhook_secret, query_request
from pep8speaks.constants import BASE_URL


class TestUtils:
    @pytest.mark.parametrize('query, method, json, data, headers, params', [
        ('/someurl', 'POST', {'k1': 'v1'}, '', {'Authorization': 'Bearer '}, None),
        ('http://someurl.com', 'GET', None, '', {'Authorization': 'Bearer ', 'h1': 'v1'}, 'k1=v1'),
    ])
    def test_request(self, mocker, query, method, json, data, headers, params):
        mock_func = mock.MagicMock(return_value=True)
        mocker.patch('requests.request', mock_func)
        query_request(query, method, json=json, data=data,
                      headers=headers, params=params)
        assert mock_func.call_count == 1
        assert mock_func.call_args[0][0] == method
        assert mock_func.call_args[1]['headers'] == headers
        assert mock_func.call_args[1]['params'] == params
        assert mock_func.call_args[1]['json'] == json
        if query[0] == "/":
            assert mock_func.call_args[0][1] == BASE_URL + query
        else:
            assert mock_func.call_args[0][1] == query

    @pytest.mark.parametrize('base, head, expected', [
        ({}, {}, {}),
        ({}, {"k1": "v1"}, {}),
        ({"k1": "v1"}, {}, {"k1": "v1"}),
        ({"k1": "v1"}, {"k1": "v2"}, {"k1": "v2"}),
        ({"k1": "v1"}, {"k1": None}, {"k1": None}),
        ({"k1": "v1"}, {"k2": "v2"}, {"k1": "v1"}),
        ({"k1": ["v1", "v2", "v3"]}, {"k1": "v1"}, {"k1": "v1"}),
        ({"k1": "v1"}, {"k1": {"k2": {'k3': 3}}}, {"k1": "v1"}),
        ({"k1": "v1"}, {"k1": ["v1", "v2", "v3"]}, {"k1": ["v1", "v2", "v3"]}),
        ({"k1": {"k2": "v1"}}, {"k1": "v1"}, {"k1": "v1"}),
        ({"k1": {"k2": "v1"}}, {"k1": {"k2": "v2"}}, {"k1": {"k2": "v2"}}),
        ({"k1": {"k2": "v1", "k3": "v2"}}, {"k1": {"k2": "v3"}}, {'k1': {'k2': 'v3', 'k3': 'v2'}}),
    ])
    def test_update_dict(self, base, head, expected):
        assert update_dict(base, head) == expected

    def test_match_webhook_secret(self, monkeypatch):
        mock_request = mock.MagicMock()

        assert match_webhook_secret(mock_request) is True

        monkeypatch.setenv('OVER_HEROKU', True)

        mock_request.headers = {'Header1': True}
        with pytest.raises(werkzeug.exceptions.Forbidden):
            match_webhook_secret(mock_request)

        mock_request.headers = {'X-Hub-Signature': None}
        with pytest.raises(werkzeug.exceptions.Forbidden):
            match_webhook_secret(mock_request)

        key, data = 'testkey', 'testdata'

        hmac_obj = hmac.new(key.encode(),
                            data.encode(),
                            digestmod="sha1")

        mock_request.headers = {
            'X-Hub-Signature': f'{hmac_obj.name}={hmac_obj.hexdigest()}'
        }
        with pytest.raises(werkzeug.exceptions.NotImplemented):
            match_webhook_secret(mock_request)

        hmac_obj = hmac.new(key.encode(),
                            data.encode(),
                            digestmod="sha1")

        mock_request.headers = {
            'X-Hub-Signature': f'sha1={hmac_obj.hexdigest()}'
        }
        mock_request.data = data.encode()

        monkeypatch.setenv('GITHUB_PAYLOAD_SECRET', 'wrongkey')
        with pytest.raises(werkzeug.exceptions.Forbidden):
            match_webhook_secret(mock_request)

        monkeypatch.setenv('GITHUB_PAYLOAD_SECRET', key)
        assert match_webhook_secret(mock_request) is True
