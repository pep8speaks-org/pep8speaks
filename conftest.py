"""Fixture configuration for pytest."""
import pytest

from server import create_app


@pytest.fixture
def app():
    # app = Flask(__name__)
    app = create_app()
    return app
