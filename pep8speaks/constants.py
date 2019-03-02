import os

# HEADERS is deprecated, use AUTH only
HEADERS = {"Authorization": "token " + os.environ.setdefault("GITHUB_TOKEN", "")}
AUTH = (os.environ.setdefault("BOT_USERNAME", ""), os.environ.setdefault("GITHUB_TOKEN", ""))
BASE_URL = 'https://api.github.com'
