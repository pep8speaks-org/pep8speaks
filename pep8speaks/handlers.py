# -*- coding: utf-8 -*-
from pep8speaks import helpers, utils, models


def handle_pull_request(request):
    ghrequest = models.GHRequest(request, request.headers["X-GitHub-Event"])

    if not ghrequest.OK:
        return utils.Response(ghrequest)

    # If the PR contains at least one Python file
    pythonic_pr = helpers.check_pythonic_pr(ghrequest.repository, ghrequest.pr_number)

    if not pythonic_pr:
        return utils.Response(ghrequest)

    helpers.update_users(ghrequest.repository)

    # Get the config from .pep8speaks.yml file of the repository
    config = helpers.get_config(ghrequest.repository, ghrequest.base_branch, ghrequest.after_commit_hash)

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
        return utils.Response(ghrequest)

    # Simply do not comment no-error messages when a PR is opened
    if not ERROR:
        if ghrequest.action == "opened":
            return utils.Response(ghrequest)
        elif ghrequest.action in ("reopened", "synchronize"):
            ONLY_UPDATE_COMMENT_BUT_NOT_CREATE = True

    # Concatenate comment parts
    comment = header + body + footer

    # Do not make duplicate comment made on the PR by the bot
    # Check if asked to keep quiet
    if not helpers.comment_permission_check(ghrequest):
        return utils.Response(ghrequest)

    # Do not run on PR's created by pep8speaks which use autopep8
    # Too much noisy
    if ghrequest.author == "pep8speaks":
        return utils.Response(ghrequest)

    # NOW, Interact with the PR and make/update the comment
    helpers.create_or_update_comment(ghrequest, comment, ONLY_UPDATE_COMMENT_BUT_NOT_CREATE)

    return utils.Response(ghrequest)


def handle_issue_comment(request):
    ghrequest = models.GHRequest(request, request.headers["X-GitHub-Event"])

    if not ghrequest.OK:
        return utils.Response(ghrequest)

    # Get the .pep8speaks.yml config file from the repository
    config = helpers.get_config(ghrequest.repository, ghrequest.base_branch, ghrequest.after_commit_hash)

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

    return utils.Response(ghrequest)


def handle_installation(request):
    """
    Do nothing. It's handled by handle_integration_installation
    """
    return utils.Response()


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

    comment = (
        f"Here you go with [the Pull Request]({ghrequest.pr_url}) ! The fixes are "
        f"suggested by [autopep8](https://github.com/hhatto/autopep8).\n\n @{ghrequest.reviewer}"
    )
    if ghrequest.reviewer != ghrequest.author:  # Both are not the same person
        comment += f" @{ghrequest.author}"

    query = f"/repos/{ghrequest.repository}/issues/{str(ghrequest.pr_number)}/comments"
    response = utils.query_request(query, method='POST', json={"body": comment})
    ghrequest.comment_response = response.json()

    return utils.Response(ghrequest)


def _create_diff(ghrequest, config):
    # Dictionary with filename matched with a string of diff
    ghrequest.diff = {}

    # Process the files and prepare the diff for the gist
    helpers.autopep8(ghrequest, config)

    # Create the gist
    helpers.create_gist(ghrequest)

    comment = (
        f"Here you go with [the gist]({ghrequest.gist_url}) !\n\n"
        f"> You can ask me to create a PR against this branch "
        f"with those fixes. Simply comment "
        f"`@pep8speaks pep8ify`.\n\n @{ghrequest.reviewer}"
    )
    if ghrequest.reviewer != ghrequest.author:  # Both are not the same person
        comment += f" @{ghrequest.author}"

    query = f"/repos/{ghrequest.repository}/issues/{str(ghrequest.pr_number)}/comments"
    response = utils.query_request(query, method='POST', json={"body": comment})
    ghrequest.comment_response = response.json()

    if ghrequest.error:
        return utils.Response(ghrequest, status=400)

    return utils.Response(ghrequest)


def handle_integration_installation(request):
    """
    Follow the user from the account of @pep8speaks on GitHub
    """
    user = request.json["sender"]["login"]
    helpers.follow_user(user)
    response_object = {
        "message": f"Followed @{user}"
    }
    return utils.Response(response_object)


def handle_integration_installation_repo(request):
    """
    Update the database of repositories the integration is working upon.
    """
    repositories = request.json["repositories_added"]

    for repo in repositories:
        helpers.update_users(repo["full_name"])

    response_object = {
        "message": f"Added the following repositories : {str(repositories)}"
    }
    return utils.Response(response_object)


def handle_ping(request):
    """
    Do nothing
    """
    return utils.Response()


def handle_unsupported_requests(request):
    response_object = {
        "unsupported github event": request.headers["X-GitHub-Event"],
    }
    return utils.Response(response_object, 400)
