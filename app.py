# -*- coding: utf-8 -*-
import os

from flask import Flask, render_template, redirect, request
from flask_session import Session

from pep8speaks import handlers, utils


def create_app():
    app = Flask(__name__)
    sess = Session()

    @app.route("/", methods=['GET', 'POST'])
    def main():
        """Main function to handle all requests."""
        if request.method == "POST":
            # GitHub sends the secret key in the payload header
            if utils.match_webhook_secret(request):
                event = request.headers["X-GitHub-Event"]
                app.logger.debug(f"Request Headers:\n{request.headers}")
                app.logger.debug(f"Request body:\n{request.json}")
                event_to_action = {
                    "pull_request": handlers.handle_pull_request,
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
                    return handlers.handle_unsupported_requests(request)
            else:
                app.logger.info("Received an unauthorized request")
                return handlers.handle_unauthorized_requests()
        else:
            return redirect("https://pep8speaks.com")

    app.secret_key = os.environ.setdefault("APP_SECRET_KEY", "")
    app.config['SESSION_TYPE'] = 'filesystem'

    sess.init_app(app)
    app.debug = False
    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
