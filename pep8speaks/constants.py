import os

# HEADERS is deprecated, use AUTH only
HEADERS = {"Authorization": "token " + os.environ.setdefault("GITHUB_TOKEN", "")}
AUTH = (os.environ.setdefault("BOT_USERNAME", ""), os.environ.setdefault("GITHUB_TOKEN", ""))

# on github enterprise, set appropriate FQDN by environment variable.
# export GH_BASE='github.example.com'
# export GH_API='github.example.com/api/v3'
# export GH_RAW='raw.github.example.com'
GH_BASE = os.environ.setdefault('GH_BASE', 'github.com')
GH_API = os.environ.setdefault('GH_API', 'api.github.com')
GH_RAW = os.environ.setdefault('GH_RAW', 'raw.githubusercontent.com')
GH_USER_ID = int(os.environ.setdefault('GH_USER_ID', '24736507'))
