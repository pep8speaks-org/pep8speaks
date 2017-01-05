# -*- coding: utf-8 -*-
import builtins
import hmac

import os
import sys
import urllib.parse as urlparse
from flask import Flask, render_template, redirect, request
from flask_session import Session
import psycopg2
from pep8speaks import handlers, helpers


if "OVER_HEROKU" in os.environ:  # For running locally
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )

    cursor = conn.cursor()

    # Make the objects available across all the modules
    builtins.conn = conn
    builtins.cursor = cursor


app = Flask(__name__)
sess = Session()


@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == "GET":
        return redirect("https://pep8speaks.com")
    elif request.method == "POST":
        if helpers.match_webhook_secret(request):
            if request.headers["X-GitHub-Event"] == "pull_request":
                return handlers.handle_pull_request(request)
    else:
        return render_template('index.html')


app.secret_key = os.environ["APP_SECRET_KEY"]
app.config['SESSION_TYPE'] = 'filesystem'

sess.init_app(app)
app.debug = False

if __name__ == '__main__':
    app.run(debug=True)
# app.run()
