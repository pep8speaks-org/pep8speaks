# -*- coding: utf-8 -*-
import json
import os

import requests
from flask import Response
from pep8speaks import helpers


def handle_pull_request(request):

    # A variable which is set to False whenever a criteria is not met
    # Ultimately if this is True, only then the comment is made
    PERMITTED_TO_COMMENT = True
    # This dictionary is used and updated after making API calls
    data = {}

    if request.json["action"] in ["synchronize", "opened", "reopened"]:
        data = {
            "after_commit_hash": request.json["pull_request"]["head"]["sha"],
            "repository": request.json["repository"]["full_name"],
            "author": request.json["pull_request"]["user"]["login"],
            "diff_url": request.json["pull_request"]["diff_url"],
            # Dictionary with filename matched with list of results
            "results": {},

            # Dictionary with filename matched with list of results caused by
            # pycodestyle arguments
            "extra_results": {},
            "pr_number": request.json["number"],
        }

        # Update users of the integration
        helpers.update_users(data["repository"])

        # Get the config from .pep8speaks.yml file of the repository
        config = helpers.get_config(data)

        # Personalising the messages obtained from the config file
        # Replace {name} with name of the author
        if "message" in config:
            for act in config["message"]:
                # can be either "opened" or "updated"
                for pos in config["message"][act]:
                    # can be either "header" or "footer"
                    msg = config["message"][act][pos]
                    new_msg = msg.replace("{name}", data["author"])
                    config["message"][act][pos] = new_msg

        # Updates data dictionary with the results
        # This function runs the pep8 checker
        helpers.run_pycodestyle(data, config)

        # Construct the comment
        header, body, footer, ERROR = helpers.prepare_comment(request, data, config)

        # If there is nothing in the comment body, no need to make the comment
        if len(body) == 0:
            PERMITTED_TO_COMMENT = False
        if config["no_blank_comment"]:  # If asked not to comment no-error messages
            if not ERROR:  # If there is no error in the PR
                PERMITTED_TO_COMMENT = False

        # Concatenate comment parts
        comment = header + body + footer

        # Do not make duplicate comment made on the PR by the bot
        # Check if asked to keep quiet
        if not helpers.comment_permission_check(data, comment):
            PERMITTED_TO_COMMENT = False

        # Do not run on PR's created by pep8speaks which use autopep8
        # Too much noisy
        if data["author"] == "pep8speaks":
            PERMITTED_TO_COMMENT = False

        # Make the comment
        if PERMITTED_TO_COMMENT:
            helpers.create_or_update_comment(data, comment)

    js = json.dumps(data)
    return Response(js, status=200, mimetype='application/json')


def handle_review(request):
    # Handle the request when a new review is submitted

    data = dict()
    data["after_commit_hash"] = request.json["pull_request"]["head"]["sha"],
    data["author"] = request.json["pull_request"]["user"]["login"]
    data["reviewer"] = request.json["review"]["user"]["login"]
    data["repository"] = request.json["repository"]["full_name"]
    data["diff_url"] = request.json["pull_request"]["diff_url"]
    data["sha"] = request.json["pull_request"]["head"]["sha"]
    data["review_url"] = request.json["review"]["html_url"]
    data["pr_number"] = request.json["pull_request"]["number"]

    # Get the .pep8speaks.yml config file from the repository
    config = helpers.get_config(data)

    condition1 = request.json["action"] == "submitted"
    # Mainly the summary of the review matters
    ## pep8speaks must be mentioned
    condition2 = "@pep8speaks" in request.json["review"]["body"]
    ## Check if asked to pep8ify
    condition3 = "pep8ify" in request.json["review"]["body"]

    ## If pep8ify is not there, all other reviews with body summary
    ## having the mention of pep8speaks, will result in commenting
    ## with autpep8 diff gist.
    conditions_matched = condition1 and condition2 and condition3

    if conditions_matched:
        return _pep8ify(request, data, config)
    else:
        conditions_matched = condition1 and condition2
        if conditions_matched:
            return _create_diff(request, data, config)


def _pep8ify(request, data, config):
    data["target_repo_fullname"] = request.json["pull_request"]["head"]["repo"]["full_name"]
    data["target_repo_branch"] = request.json["pull_request"]["head"]["ref"]
    data["results"] = {}

    # Check if the fork of the target repo exists
    # If yes, then delete it
    helpers.delete_if_forked(data)
    # Fork the target repository
    helpers.fork_for_pr(data)
    # Update the fork description. This helps in fast deleting it
    helpers.update_fork_desc(data)
    # Create a new branch for the PR
    helpers.create_new_branch(data)
    # Fix the errors in the files
    helpers.autopep8ify(data, config)
    # Commit each change onto the branch
    helpers.commit(data)
    # Create a PR from the branch to the target repository
    helpers.create_pr(data)

    js = json.dumps(data)
    return Response(js, status=200, mimetype='application/json')


def _create_diff(request, data, config):
    # Dictionary with filename matched with a string of diff
    data["diff"] = {}

    # Process the files and prepare the diff for the gist
    helpers.autopep8(data, config)

    # Create the gist
    helpers.create_gist(data, config)

    comment = "Here you go with [the gist]({}) !\n\n" + \
              "> You can ask me to create a PR against this branch " + \
              "with those fixes. Submit a review comment as " + \
              "`@pep8speaks pep8ify`.\n\n"
    if data["reviewer"] == data["author"]:  # Both are the same person
        comment += "@{} "
        comment = comment.format(data["gist_url"], data["reviewer"])
    else:
        comment += "@{} @{} "
        comment = comment.format(data["gist_url"], data["reviewer"],
                                 data["author"])

    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    query = "https://api.github.com/repos/{}/issues/{}/comments"
    query = query.format(data["repository"], str(data["pr_number"]))
    response = requests.post(query, json={"body": comment}, headers=headers, auth=auth)
    data["comment_response"] = response.json()

    status_code = 200
    if "error" in data:
        status_code = 400
    js = json.dumps(data)
    return Response(js, status=status_code, mimetype='application/json')


def handle_review_comment(request):
    # Figure out what does "position" mean in the response
    pass


def handle_integration_installation(request):
    # Follow user
    data = {
        "user": request.json["sender"]["login"]
    }

    helpers.follow_user(data["user"])
    status_code = 200
    js = json.dumps(data)
    return Response(js, status=status_code, mimetype='application/json')


def handle_integration_installation_repo(request):
    # Add the repo in the database
    data = {
        "repositories": request.json["repositories_added"],
    }

    for repo in data["repositories"]:
        helpers.update_users(repo["full_name"])
    status_code = 200
    js = json.dumps(data)
    return Response(js, status=status_code, mimetype='application/json')


def handle_ping(request):
    return Response(status=200, mimetype='application/json')


def handle_unsupported_requests(request):
    data = {
        "unsupported github event": request.headers["X-GitHub-Event"],
    }
    js = json.dumps(data)
    return Response(js, status=400, mimetype='application/json')
