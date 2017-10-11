import hmac
import pytest
import werkzeug
from pep8speaks.utils import update_dict, match_webhook_secret


class TestUtils:

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

    def test_match_webhook_secret(self, monkeypatch, request_ctx):
        assert match_webhook_secret(request_ctx) is True

        monkeypatch.setenv('OVER_HEROKU', False)

        request_ctx.headers = {'Header1': True}
        with pytest.raises(werkzeug.exceptions.Forbidden):
            match_webhook_secret(request_ctx)

        request_ctx.headers = {'X-Hub-Signature': None}
        with pytest.raises(werkzeug.exceptions.Forbidden):
            match_webhook_secret(request_ctx)

        key, data = 'testkey', 'testdata'

        hmac_obj = hmac.new(key.encode(),
                            data.encode())

        request_ctx.headers = {
            'X-Hub-Signature': '{}={}'.format(hmac_obj.name,
                                              hmac_obj.hexdigest())
        }
        with pytest.raises(werkzeug.exceptions.NotImplemented):
            match_webhook_secret(request_ctx)

        hmac_obj = hmac.new(key.encode(),
                            data.encode(),
                            digestmod="sha1")

        request_ctx.headers = {
            'X-Hub-Signature': 'sha1={}'.format(hmac_obj.hexdigest())
        }
        request_ctx.data = data.encode()

        monkeypatch.setenv('GITHUB_PAYLOAD_SECRET', 'wrongkey')
        with pytest.raises(werkzeug.exceptions.Forbidden):
            match_webhook_secret(request_ctx)

        monkeypatch.setenv('GITHUB_PAYLOAD_SECRET', key)
        assert match_webhook_secret(request_ctx) is True
