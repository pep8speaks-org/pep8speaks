import pytest
from flask import Flask
from app import create_app


@pytest.fixture
def app():
    # app = Flask(__name__)
    app = create_app()
    return app
