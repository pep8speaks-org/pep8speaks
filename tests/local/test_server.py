import pytest
import mock
from flask import url_for


class TestApp:

    def test_main_get(self, client):
        response = client.get(url_for('main'))
        assert response.status_code == 302
        assert response.location == 'https://pep8speaks.org'

    @pytest.mark.parametrize('event, action', [
        ("pull_request", "handle_pull_request"),
        ("integration_installation", "handle_integration_installation"),
        ("integration_installation_repositories", "handle_integration_installation_repo"),
        ("installation_repositories", "handle_integration_installation_repo"),
        ("ping", "handle_ping"),
        ("issue_comment", "handle_issue_comment"),
        ("installation", "handle_installation"),
        ("some_strage_event", "handle_unsupported_requests"),
    ])
    def test_main_post(self, mocker, client, event, action):
        mock_func = mock.MagicMock(return_value=True)
        mocker.patch('pep8speaks.utils.match_webhook_secret', mock_func)
        mocker.patch('pep8speaks.handlers.' + action, mock_func)
        client.post(url_for('main'),
                    headers={"X-GitHub-Event": event})
        assert mock_func.call_count == 2
