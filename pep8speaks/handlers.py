# -*- coding: utf-8 -*-
import json
import os

import requests
from flask import Response as FResponse
from pep8speaks import helpers, utils


def Response(data={}, status=200, mimetype='application/json'):
    response_object = json.dumps(data, default=lambda obj: obj.__dict__)
    return FResponse(response_object, status=status, mimetype=mimetype)



def handle_pull_request(ghrequest):

    # A variable which is set to False whenever a criteria is not met
    # Ultimately if this is True, only then the comment is made

    if not ghrequest.OK:
        return Response(ghrequest)

    # If the PR contains at least one Python file
    pythonic_pr = helpers.check_pythonic_pr(ghrequest.repository, ghrequest.pr_number)

    if not pythonic_pr:
        return Response(ghrequest)

    helpers.update_users(ghrequest.repository)

    # Get the config from .pep8speaks.yml file of the repository
    config = helpers.get_config(ghrequest.repository, ghrequest.base_branch)

    # Personalising the messages obtained from the config file
    # Replace {name} with name of the author
    if "message" in config:
        for act in ['opened', 'updated']:
            # can be either "opened" or "updated"
            for pos in config["message"][act]:
                # can be either "header" or "footer"
                msg = config["message"][act][pos]
                new_msg = msg.replace("{name}", ghrequest.author)
                config["message"][act][pos] = new_msg

    # Updates ghrequest with the results
    # This function runs pycodestyle
    helpers.run_pycodestyle(ghrequest, config)

    # Construct the comment
    header, body, footer, ERROR = helpers.prepare_comment(ghrequest, config)

    # If there is nothing in the comment body, no need to make the comment
    # But in case of PR update, make sure to update the comment with no issues.
    ONLY_UPDATE_COMMENT_BUT_NOT_CREATE = False
    if len(body) == 0:
        return Response(ghrequest)

    # Simply do not comment no-error messages when a PR is opened
    if not ERROR:
        if ghrequest.action == "opened":
            return Response(ghrequest)
        elif ghrequest.action in ("reopened", "synchronize"):
            ONLY_UPDATE_COMMENT_BUT_NOT_CREATE = True

    # Concatenate comment parts
    comment = header + body + footer

    # Do not make duplicate comment made on the PR by the bot
    # Check if asked to keep quiet
    if not helpers.comment_permission_check(ghrequest):
        return Response(ghrequest)

    # Do not run on PR's created by pep8speaks which use autopep8
    # Too much noisy
    if ghrequest.author == "pep8speaks":
        return Response(ghrequest)

    # NOW, Interact with the PR and make/update the comment
    helpers.create_or_update_comment(ghrequest, comment, ONLY_UPDATE_COMMENT_BUT_NOT_CREATE)

    return Response(ghrequest)


def handle_installation(request):
    """
    Do nothing. It's handled by handle_integration_installation
    """
    return Response()


def handle_review(ghrequest):
    """
    Handle the request when a new review is submitted
    """

    if not ghrequest.review_body:
        return Response(ghrequest)

    # Get the .pep8speaks.yml config file from the repository
    config = helpers.get_config(ghrequest.repository, ghrequest.base_branch)

    condition1 = ghrequest.action == "submitted"
    # Mainly the summary of the review matters
    ## pep8speaks must be mentioned
    condition2 = "@pep8speaks" in ghrequest.review_body
    ## Check if asked to pep8ify
    condition3 = "pep8ify" in ghrequest.review_body

    ## If pep8ify is not there, all other reviews with body summary
    ## having the mention of pep8speaks, will result in commenting
    ## with autpep8 diff gist.
    conditions_matched = condition1 and condition2 and condition3

    if conditions_matched:
        return _pep8ify(ghrequest, config)
    else:
        conditions_matched = condition1 and condition2
        if conditions_matched:
            return _create_diff(ghrequest, config)
        else:
            return Response(ghrequest)


def _pep8ify(ghrequest, config):
    ghrequest.target_repo_fullname = ghrequest.pull_request["head"]["repo"]["full_name"]
    ghrequest.target_repo_branch = ghrequest.pull_request["head"]["ref"]
    ghrequest.results = {}

    # Check if the fork of the target repo exists
    # If yes, then delete it
    helpers.delete_if_forked(ghrequest)
    # Fork the target repository
    helpers.fork_for_pr(ghrequest)
    # Update the fork description. This helps in fast deleting it
    helpers.update_fork_desc(ghrequest)
    # Create a new branch for the PR
    helpers.create_new_branch(ghrequest)
    # Fix the errors in the files
    helpers.autopep8ify(ghrequest, config)
    # Commit each change onto the branch
    helpers.commit(ghrequest)
    # Create a PR from the branch to the target repository
    helpers.create_pr(ghrequest)

    comment = "Here you go with [the Pull Request]({}) ! The fixes are " \
              "suggested by [autopep8](https://github.com/hhatto/autopep8).\n\n"
    if ghrequest.reviewer == ghrequest.author:  # Both are the same person
        comment += "@{} "
        comment = comment.format(ghrequest.pr_url, ghrequest.reviewer)
    else:
        comment += "@{} @{} "
        comment = comment.format(ghrequest.pr_url, ghrequest.reviewer,
                                 ghrequest.author)

    query = "https://api.github.com/repos/{}/issues/{}/comments"
    query = query.format(ghrequest.repository, str(ghrequest.pr_number))
    response = utils._request(query, type='POST', json={"body": comment})
    ghrequest.comment_response = response.json()

    return Response(ghrequest)


def _create_diff(ghrequest, config):
    # Dictionary with filename matched with a string of diff
    ghrequest.diff = {}

    # Process the files and prepare the diff for the gist
    helpers.autopep8(ghrequest, config)

    # Create the gist
    helpers.create_gist(ghrequest, config)

    comment = "Here you go with [the gist]({}) !\n\n" + \
              "> You can ask me to create a PR against this branch " + \
              "with those fixes. Simply comment " + \
              "`@pep8speaks pep8ify`.\n\n"
    if ghrequest.reviewer == ghrequest.author:  # Both are the same person
        comment += "@{} "
        comment = comment.format(ghrequest.gist_url, ghrequest.reviewer)
    else:
        comment += "@{} @{} "
        comment = comment.format(ghrequest.gist_url, ghrequest.reviewer,
                                 ghrequest.author)

    query = "https://api.github.com/repos/{}/issues/{}/comments"
    query = query.format(ghrequest.repository, str(ghrequest.pr_number))
    response = utils._request(query, type='POST', json={"body": comment})
    ghrequest.comment_response = response.json()

    if "error" in ghrequest:
        return Response(ghrequest, status=400)

    return Response(ghrequest)


def handle_review_comment(request):
    # Figure out what does "position" mean in the response
    return Response()


def handle_integration_installation(request):
    """
    Follow the user from the account of @pep8speaks on GitHub
    """
    user = request.json["sender"]["login"]
    helpers.follow_user(user)
    response_object = {
        "message": "Followed @{}".format(user)
    }
    return Response(response_object)


def handle_integration_installation_repo(request):
    """
    Update the database of repositories the integration is working upon.
    """
    repositories = request.json["repositories_added"],

    for repo in repositories:
        helpers.update_users(repo["full_name"])

    response_object = {
        "message", "Added the following repositories : {}".format(str(repositories))
    }
    return Response(response_object)


def handle_ping(request):
    """
    Do nothing
    """
    return Response()


def handle_issue_comment(ghrequest):
    # A variable which is set to False whenever a criteria is not met
    # Ultimately if this is True, only then the comment is made
    PERMITTED_TO_COMMENT = True

    if not ghrequest.OK:
        return Response(ghrequest)

    # Get the .pep8speaks.yml config file from the repository
    config = helpers.get_config(ghrequest.repository, ghrequest.base_branch)

    splitted_comment = ghrequest.comment.lower().split()

    # If diff is required
    params1 = ["@pep8speaks", "suggest", "diff"]
    condition1 = all(p in splitted_comment for p in params1)
    # If asked to pep8ify
    params2 = ["@pep8speaks", "pep8ify"]
    condition2 = all(p in splitted_comment for p in params2)

    if condition1:
        return _create_diff(ghrequest, config)
    elif condition2:
        return _pep8ify(ghrequest, config)

    return Response(ghrequest)


def handle_unsupported_requests(request):
    response_object = {
        "unsupported github event": request.headers["X-GitHub-Event"],
    }
    return Response(response_object, 400)
