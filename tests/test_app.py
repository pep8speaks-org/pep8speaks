import pytest
import mock
from flask import url_for


class TestApp:

    def test_main_get(self, client):
        response = client.get(url_for('main'))
        assert response.status_code == 302
        assert response.location == 'https://pep8speaks.com'
