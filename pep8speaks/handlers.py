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


def handle_review(request):
    condition1 = request.json["action"] == "submitted"
    condition2 = "@pep8speaks" in request.json["review"]["body"]
    condition3 = "pep8ify" in request.json["review"]["body"]
    conditions_matched = condition1 and condition2 and condition3

    if conditions_matched:
        return _pep8ify(request)
    else:
        conditions_matched = condition1 and condition2
        if conditions_matched:
            return _create_diff(request)


def _create_diff(request):
    data = dict()
    data["author"] = request.json["pull_request"]["user"]["login"]
    data["reviewer"] = request.json["review"]["user"]["login"]
    data["repository"] = request.json["repository"]["full_name"]
    data["diff_url"] = request.json["pull_request"]["diff_url"]
    data["sha"] = request.json["pull_request"]["head"]["sha"]
    data["review_url"] = request.json["review"]["html_url"]
    data["pr_number"] = request.json["pull_request"]["number"]
    # Dictionary with filename matched with a string of diff
    data["diff"] = {}

    # Get the .pep8speaks.yml config file from the repository
    config = helpers.get_config(data["repository"])

    helpers.autopep8(data, config)

    helpers.create_gist(data, config)

    comment = "Here you go with [the gist]({}) !\n\n" + \
              "> You can ask me to create a PR against this branch " + \
              "with those fixes. Submit a review comment as " + \
              "`@pep8speaks pep8ify`.\n\n" + "@{} @{} "
    comment = comment.format(data["gist_url"], data["reviewer"],
                             data["author"])

    query = "https://api.github.com/repos/" + data["repository"] + \
            "/issues/" + str(data["pr_number"]) + "/comments" + \
            "?access_token={}".format(os.environ["GITHUB_TOKEN"])
    response = requests.post(query, json={"body": comment}).json()
    data["comment_response"] = response

    js = json.dumps(data)
    return Response(js, status=200, mimetype='application/json')


def handle_review_comment(request):
    # Figure out what does "position" mean in the response
    pass
