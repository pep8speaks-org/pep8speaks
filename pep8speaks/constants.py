import os

# HEADERS is deprecated, use AUTH only
HEADERS = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
AUTH = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
BASE_URL = 'https://api.github.com'
