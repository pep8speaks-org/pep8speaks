# -*- coding: utf-8 -*-
import json
import os
from flask import Response
import requests
from pep8speaks import helpers

def handle_pull_request(request):

    # A variable which is set to False whenever a criteria is not met
    PERMITTED_TO_COMMENT = True

    if request.json["action"] in ["synchronize", "opened", "reopened"]:
        after_commit_hash = request.json["pull_request"]["head"]["sha"]
        repository = request.json["repository"]["full_name"]
        author = request.json["pull_request"]["user"]["login"]
        diff_url = request.json["pull_request"]["diff_url"]
        pr_number = request.json["number"]
        helpers.update_users(repository)  # Update users of the repository
        data = {
            "after_commit_hash": after_commit_hash,
            "repository": repository,
            "author": author,
            "diff_url": diff_url,
            # Dictionary with filename matched with list of results
            "results": {},
            "pr_number": pr_number,
        }

        config = helpers.get_config(repository)

        # personalising the messages
        if "message" in config:
            for act in config["message"]:
                # can be either "opened" or "updated"
                for pos in config["message"][act]:
                    # can be either "header" or "footer"
                    msg = config["message"][act][pos]
                    new_msg = msg.replace("{name}", author)
                    config["message"][act][pos] = new_msg


        # Updates data dictionary with the results
        helpers.run_pycodestyle(data, config)

        # Construct the comment
        header, body, footer = helpers.prepare_comment(request, data, config)

        if len(body) == 0:
            PERMITTED_TO_COMMENT = False

        comment = header + body + footer

        # Do not make duplicate comment made on the PR by the bot
        PERMITTED_TO_COMMENT = helpers.comment_permission_check(data, comment)

        # Make the comment
        if PERMITTED_TO_COMMENT:
            query = "https://api.github.com/repos/" + repository + "/issues/" + \
                    str(data["pr_number"]) + "/comments?access_token={}".format(
                        os.environ["GITHUB_TOKEN"])
            response = requests.post(query, json={"body": comment}).json()
            data["comment_response"] = response

        js = json.dumps(data)
        return Response(js, status=200, mimetype='application/json')
