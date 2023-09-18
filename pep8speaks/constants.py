import os
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
BASE_URL = 'https://api.github.com'
FLASK_DEBUG=0