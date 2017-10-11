# -*- coding: utf-8 -*-
import builtins
import os
import urllib.parse as urlparse

import psycopg2
from flask import Flask, render_template, redirect, request
from flask_session import Session

from pep8speaks import handlers, utils


def create_app():
    # For running locally without connecting to the database
    if os.environ.get("OVER_HEROKU", False) is not False:
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
            # GitHub sends the secret key in the payload header
            if utils.match_webhook_secret(request):
                event = request.headers["X-GitHub-Event"]
                event_to_action = {
                    "pull_request": handlers.handle_pull_request,
                    "pull_request_review": handlers.handle_review,
                    "pull_request_review_comment": handlers.handle_review_comment,
                    "integration_installation": handlers.handle_integration_installation,
                    "integration_installation_repositories": handlers.handle_integration_installation_repo,
                    "installation_repositories": handlers.handle_integration_installation_repo,
                    "ping": handlers.handle_ping,
                    "issue_comment": handlers.handle_issue_comment,
                    "installation": handlers.handle_installation,
                }
                try:
                    return event_to_action[event](request)
                except KeyError:
                    handlers.handle_unsupported_requests(request)
        else:
            return render_template('index.html')

    app.secret_key = os.environ.setdefault("APP_SECRET_KEY", "")
    app.config['SESSION_TYPE'] = 'filesystem'

    sess.init_app(app)
    app.debug = False
    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
