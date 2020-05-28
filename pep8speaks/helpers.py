# -*- coding: utf-8 -*-

import base64
import configparser
import datetime
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import time

import unidiff
import yaml
from pep8speaks import utils


def update_users(repository):
    """Star the repository from the bot account"""
    headers = {
        "Content-Length": "0",
    }
    query = f"/user/starred/{repository}"
    return utils.query_request(query=query, method='PUT', headers=headers)


def follow_user(user):
    """Follow the user of the service"""
    headers = {
        "Content-Length": "0",
    }
    query = f"/user/following/{user}"
    return utils.query_request(query=query, method='PUT', headers=headers)


def read_setup_cfg_file(setup_config_file):
    """Return a dictionary for pycodestyle/flake8 section"""
    setup_config = configparser.ConfigParser()
    setup_config.read_string(setup_config_file)

    setup_config_found = False
    if setup_config.has_section("pycodestyle"):
        setup_config_section = setup_config["pycodestyle"]
        setup_config_found = True
    elif setup_config.has_section("flake8"):
        setup_config_section = setup_config["flake8"]
        setup_config_found = True

    linter_cfg_config = {}

    if not setup_config_found:
        return linter_cfg_config

    # These ones are of type string
    keys = ["max-line-length", "count", "first", "show-pep8", "show-source", "statistics", "hang-closing"]
    for key in keys:
        try:
            value = setup_config_section[key]
            value = value.split(" ")[0].strip(",#")  # In case there are comments on the line
            if key == "max-line-length":
                value = int(value)
            linter_cfg_config[key] = value
        except KeyError:
            pass

    list_keys = ["ignore", "exclude", "filename", "select"]
    for key in list_keys:
        try:
            value = setup_config_section[key]
            items = []
            for line in value.split("\n"):
                item = line.split(" ")[0].strip(",#")
                if len(item) > 0:
                    items.append(item)
                    linter_cfg_config[key] = items
        except KeyError:
            pass

    return linter_cfg_config


def get_config(repo, base_branch, after_commit_hash):
    """
    Get .pep8speaks.yml config file from the repository and return
    the config dictionary

    First look in the base branch of the Pull Request (general master branch).
    If no file is found, then look for a file in the head branch of the Pull Request.
    """

    # Default configuration parameters
    default_config = Path(__file__).absolute().parent.parent.joinpath("data", "default_pep8speaks.yml")
    with open(default_config, "r") as config_file:
        config = yaml.safe_load(config_file)

    linters = ["pycodestyle", "flake8"]

    # Read setup.cfg for [pycodestyle] or [flake8] section
    setup_config_file = ""
    query = f"https://raw.githubusercontent.com/{repo}/{base_branch}/setup.cfg"
    r = utils.query_request(query)
    if r.status_code == 200:
        setup_config_file = r.text
    else:  # Try to look for a config in the head branch of the Pull Request
        new_query = f"https://raw.githubusercontent.com/{repo}/{after_commit_hash}/setup.cfg"
        r_new = utils.query_request(new_query)
        if r_new.status_code == 200:
            setup_config_file = r_new.text

    if len(setup_config_file) > 0:
        linter_cfg_config = read_setup_cfg_file(setup_config_file)
        # Copy the setup.cfg config for all linters
        new_setup_config = {}
        for linter in linters:
            new_setup_config[linter] = linter_cfg_config
        config = utils.update_dict(config, new_setup_config)

    # Read .pep8speaks.yml
    new_config_text = ""

    # Configuration file
    query = f"https://raw.githubusercontent.com/{repo}/{base_branch}/.pep8speaks.yml"
    r = utils.query_request(query)

    if r.status_code == 200:
        new_config_text = r.text
    else:  # Try to look for a config in the head branch of the Pull Request
        new_query = f"https://raw.githubusercontent.com/{repo}/{after_commit_hash}/.pep8speaks.yml"
        r_new = utils.query_request(new_query)
        if r_new.status_code == 200:
            new_config_text = r_new.text

    if len(new_config_text) > 0:
        try:
            new_config = yaml.load(new_config_text)
            # overloading the default configuration with the one specified
            config = utils.update_dict(config, new_config)
        except yaml.YAMLError:  # Bad YAML file
            pass

    # Create pycodestyle and flake8 command line arguments
    for linter in linters:
        confs = config.get(linter, dict())
        arguments = []
        for key, value in confs.items():
            if value:  # Non empty
                if isinstance(value, int):
                    if isinstance(value, bool):
                        arguments.append(f"--{key}")
                    else:
                        arguments.append(f"--{key}={value}")
                elif isinstance(value, list):
                    arguments.append(f"--{key}={','.join(value)}")
        config[f"{linter}_cmd_config"] = f' {" ".join(arguments)}'

    # linters are case-sensitive with error codes
    for linter in linters:
        if config[linter]["ignore"]:
            config[linter]["ignore"] = [e.upper() for e in list(config[linter]["ignore"])]

    return config


def get_files_involved_in_pr(repo, pr_number):
    """
    Return a list of file names modified/added in the PR
    """
    headers = {"Accept": "application/vnd.github.VERSION.diff"}

    query = f"/repos/{repo}/pulls/{pr_number}"
    r = utils.query_request(query, headers=headers)

    patch = unidiff.PatchSet(r.content.splitlines(), encoding=r.encoding)

    files = {}

    for patchset in patch:
        diff_file = patchset.target_file[1:]
        files[diff_file] = []
        for hunk in patchset:
            for line in hunk.target_lines():
                if line.is_added:
                    files[diff_file].append(line.target_line_no)
    return files


def get_py_files_in_pr(repo, pr_number, exclude=None):
    if exclude is None:
        exclude = []
    files = get_files_involved_in_pr(repo, pr_number)
    for diff_file in list(files.keys()):
        if diff_file[-3:] != ".py" or utils.filename_match(diff_file, exclude):
            del files[diff_file]

    return files


def check_pythonic_pr(repo, pr_number):
    """
    Return True if the PR contains at least one Python file
    """
    return len(get_py_files_in_pr(repo, pr_number)) > 0


def run_pycodestyle(ghrequest, config):
    """
    Runs the linter cli tool on the files and update ghrequest
    """
    linter = config["scanner"]["linter"]  # Either pycodestyle or flake8
    repo = ghrequest.repository
    pr_number = ghrequest.pr_number
    commit = ghrequest.after_commit_hash

    # Run linter
    ## All the python files with additions
    # A dictionary with filename paired with list of new line numbers
    files_to_exclude = config[linter]["exclude"]
    py_files = get_py_files_in_pr(repo, pr_number, files_to_exclude)

    ghrequest.links = {}  # UI Link of each updated file in the PR
    for py_file in py_files:
        filename = py_file[1:]
        query = f"https://raw.githubusercontent.com/{repo}/{commit}/{py_file}"
        r = utils.query_request(query)
        with open("file_to_check.py", 'w+', encoding=r.encoding) as file_to_check:
            file_to_check.write(r.text)

        # Use the command line here
        if config["scanner"]["linter"] == "flake8":
            cmd = f'flake8 {config["flake8_cmd_config"]} file_to_check.py'
        else:
            cmd = f'pycodestyle {config["pycodestyle_cmd_config"]} file_to_check.py'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        ghrequest.extra_results[filename] = stdout.decode(r.encoding).splitlines()

        # Put only relevant errors in the ghrequest.results dictionary
        ghrequest.results[filename] = []
        for error in list(ghrequest.extra_results[filename]):
            relevant_error_pattern = r"^file_to_check.py:\d+:\d+:\s[WEF]\d+\s.*"
            # Other error codes are B C D T
            if re.search(relevant_error_pattern, error):
                ghrequest.results[filename].append(error.replace("file_to_check.py", filename))
                ghrequest.extra_results[filename].remove(error)

        # Replace file_to_check.py with filename in all additional errors
        extras = ghrequest.extra_results[filename]
        ghrequest.extra_results[filename] = [e.replace("file_to_check.py", filename) for e in extras]

        ## Remove errors in case of diff_only = True
        ## which are caused in the whole file
        for error in list(ghrequest.results[filename]):
            if config["scanner"]["diff_only"]:
                if not int(error.split(":")[1]) in py_files[py_file]:
                    ghrequest.results[filename].remove(error)

        ## Store the link to the file
        url = f"https://github.com/{repo}/blob/{commit}{py_file}"
        ghrequest.links[filename + "_link"] = url
        os.remove("file_to_check.py")


def prepare_comment(ghrequest, config):
    """Construct the string of comment i.e. its header, body and footer."""
    author = ghrequest.author
    # Write the comment body
    # ## Header
    comment_header = ""
    action_text = None
    if ghrequest.action == "opened":
        action_text = "opening"
    elif ghrequest.action in ["synchronize", "reopened"]:
        action_text = "updating"
    if action_text:
        comment_header = config["message"][action_text[:-3] + "ed"]["header"]
        if comment_header == "":
            comment_header = (
                "Hello @{author!s}! Thanks for {action_text} this PR. "
                "We checked the lines you've touched for [PEP\N{NBSP}8]"
                "(https://www.python.org/dev/peps/pep-0008) issues, and found:"
                .format(author=author, action_text=action_text))
        comment_header = comment_header + "\n\n"

    # ## Body
    ERROR = False  # Set to True when any pep8 error exists
    comment_body = []
    for gh_file, issues in ghrequest.results.items():
        if not issues:
            if not config["only_mention_files_with_errors"]:
                comment_body.append(
                    f"* In the file [`{gh_file}`]({ghrequest.links[gh_file + '_link']}): No issues found.")
        else:
            ERROR = True
            comment_body.append(
                f"* In the file [`{gh_file}`]({ghrequest.links[gh_file + '_link']}):\n"
            )
            if config["descending_issues_order"]:
                issues = issues[::-1]

            for issue in issues:
                # Replace filename with L
                error_string = issue.replace(gh_file + ":", "Line ")

                # Link error codes to search query
                error_string_list = error_string.split(" ")
                code = error_string_list[2]
                code_url = f"https://duckduckgo.com/?q=pep8%20{code}"
                error_string_list[2] = f"[{code}]({code_url})"

                # Link line numbers in the file
                line, col = error_string_list[1][:-1].split(":")
                line_url = ghrequest.links[gh_file + "_link"] + "#L" + line
                error_string_list[1] = f"[{line}:{col}]({line_url}):"
                error_string = " ".join(error_string_list)
                error_string = error_string.replace("Line [", "[Line ")
                comment_body.append(f"\n> {error_string}")

        comment_body.append("\n\n")
        if ghrequest.extra_results[gh_file]:
            logging.debug("There are extra results which are not being printed.")
            logging.debug(ghrequest.extra_results[gh_file])
            # comment_body.append("* Additional results for this file:\n\n> ")
            # comment_body.append(
            #     "\n> ".join(ghrequest.extra_results[gh_file]))
            # comment_body.append("\n---\n\n")
            # Extra results are disabled now because flake8 generates a lot of error codes
            # The acceptable ones are listed in relevant_error_pattern in run_pycodestyle

    if config["only_mention_files_with_errors"] and not ERROR:
        comment_body.append(config["message"]["no_errors"])

    comment_body = ''.join(comment_body)

    # ## Footer
    comment_footer = []
    if action_text:
        comment_footer.append(
            config["message"][action_text[:-3] + "ed"]["footer"])

    comment_footer = ''.join(comment_footer)

    return comment_header, comment_body, comment_footer, ERROR


def comment_permission_check(ghrequest):
    """
    Check for quite and resume status or duplicate comments
    """
    repository = ghrequest.repository

    # Check for duplicate comment
    url = f"/repos/{repository}/issues/{str(ghrequest.pr_number)}/comments"
    comments = utils.query_request(url).json()

    # # Get the last comment by the bot
    # last_comment = ""
    # for old_comment in reversed(comments):
    #     if old_comment["user"]["id"] == 24736507:  # ID of @pep8speaks
    #         last_comment = old_comment["body"]
    #         break

    # # Disabling this because only a single comment is made per PR
    # text1 = ''.join(BeautifulSoup(markdown(comment)).findAll(text=True))
    # text2 = ''.join(BeautifulSoup(markdown(last_comment)).findAll(text=True))
    # if text1 == text2.replace("submitting", "updating"):
    #     PERMITTED_TO_COMMENT = False

    # Check if the bot is asked to keep quiet
    for old_comment in reversed(comments):
        if '@pep8speaks' in old_comment['body']:
            if 'resume' in old_comment['body'].lower():
                break
            elif 'quiet' in old_comment['body'].lower():
                return False

    # Check for [skip pep8]
    ## In commits
    commits = utils.query_request(ghrequest.commits_url).json()
    for commit in commits:
        if any(m in commit["commit"]["message"].lower() for m in ["[skip pep8]", "[pep8 skip]"]):
            return False
    ## PR title
    if any(m in ghrequest.pr_title.lower() for m in ["[skip pep8]", "[pep8 skip]"]):
        return False
    ## PR description
    if ghrequest.pr_desc:
        if any(m in ghrequest.pr_desc.lower() for m in ["[skip pep8]", "[pep8 skip]"]):
            return False

    return True


def create_or_update_comment(ghrequest, comment, ONLY_UPDATE_COMMENT_BUT_NOT_CREATE):
    query = f"/repos/{ghrequest.repository}/issues/{str(ghrequest.pr_number)}/comments"
    comments = utils.query_request(query).json()

    # Get the last comment id by the bot
    last_comment_id = None
    for old_comment in comments:
        if old_comment["user"]["login"] == os.environ["BOT_USERNAME"]:
            last_comment_id = old_comment["id"]
            break

    if last_comment_id is None and not ONLY_UPDATE_COMMENT_BUT_NOT_CREATE:  # Create a new comment
        response = utils.query_request(query=query, method='POST', json={"body": comment})
        ghrequest.comment_response = response.json()
    else:  # Update the last comment
        utc_time = datetime.datetime.utcnow()
        time_now = utc_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        comment += f"\n\n##### Comment last updated at {time_now!s}"

        query = f"/repos/{ghrequest.repository}/issues/comments/{str(last_comment_id)}"
        response = utils.query_request(query, method='PATCH', json={"body": comment})

    return response


def autopep8(ghrequest, config):
    # Run pycodestyle

    r = utils.query_request(ghrequest.diff_url)
    ## All the python files with additions
    patch = unidiff.PatchSet(r.content.splitlines(), encoding=r.encoding)

    # A dictionary with filename paired with list of new line numbers
    py_files = {}

    for patchset in patch:
        if patchset.target_file[-3:] == '.py':
            py_file = patchset.target_file[1:]
            py_files[py_file] = []
            for hunk in patchset:
                for line in hunk.target_lines():
                    if line.is_added:
                        py_files[py_file].append(line.target_line_no)

    # Ignore errors and warnings specified in the config file
    to_ignore = ",".join(config["pycodestyle"]["ignore"])
    arg_to_ignore = ""
    if len(to_ignore) > 0:
        arg_to_ignore = "--ignore " + to_ignore

    for py_file in py_files:
        filename = py_file[1:]
        url = f"https://raw.githubusercontent.com/{ghrequest.repository}/{ghrequest.sha}/{py_file}"
        r = utils.query_request(url)
        with open("file_to_fix.py", 'w+', encoding=r.encoding) as file_to_fix:
            file_to_fix.write(r.text)

        cmd = f'autopep8 file_to_fix.py --diff {arg_to_ignore}'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        ghrequest.diff[filename] = stdout.decode(r.encoding)

        # Fix the errors
        ghrequest.diff[filename] = ghrequest.diff[filename].replace("file_to_check.py", filename)
        ghrequest.diff[filename] = ghrequest.diff[filename].replace("\\", "\\\\")

        ## Store the link to the file
        ghrequest.links = {}
        ghrequest.links[filename + "_link"] = f"https://github.com/{ghrequest.repository}/blob/{ghrequest.sha}{py_file}"
        os.remove("file_to_fix.py")


def create_gist(ghrequest):
    """Create gists for diff files"""
    request_json = {}
    request_json["public"] = True
    request_json["files"] = {}
    request_json["description"] = f"In response to @{ghrequest.reviewer}'s comment: {ghrequest.review_url}"

    for diff_file, diffs in ghrequest.diff.items():
        if len(diffs) != 0:
            request_json["files"][diff_file.split("/")[-1] + ".diff"] = {
                "content": diffs
            }

    # Call github api to create the gist
    query = "/gists"
    response = utils.query_request(query, method='POST', json=request_json).json()
    ghrequest.gist_response = response
    ghrequest.gist_url = response["html_url"]


def delete_if_forked(ghrequest):
    FORKED = False
    query = "/user/repos"
    r = utils.query_request(query)
    for repo in r.json():
        if repo["description"]:
            if ghrequest.target_repo_fullname in repo["description"]:
                FORKED = True
                url = f"/repos/{repo['full_name']}"
                utils.query_request(url, method='DELETE')
    return FORKED


def fork_for_pr(ghrequest):
    query = f"/repos/{ghrequest.target_repo_fullname}/forks"
    r = utils.query_request(query, method='POST')

    if r.status_code == 202:
        ghrequest.fork_fullname = r.json()["full_name"]
        return True

    ghrequest.error = "Unable to fork"
    return False


def update_fork_desc(ghrequest):
    # Check if forked (takes time)
    query = f"/repos/{ghrequest.fork_fullname}"
    r = utils.query_request(query)
    ATTEMPT = 0
    while(r.status_code != 200):
        time.sleep(5)
        r = utils.query_request(query)
        ATTEMPT += 1
        if ATTEMPT > 10:
            ghrequest.error = "Forking is taking longer than usual"
            break

    full_name = ghrequest.target_repo_fullname
    author, name = full_name.split("/")
    request_json = {
        "name": name,
        "description": f"Forked from @{author}'s {full_name}"
    }
    r = utils.query_request(query, method='PATCH', data=json.dumps(request_json))
    if r.status_code != 200:
        ghrequest.error = "Could not update description of the fork"


def create_new_branch(ghrequest):
    query = f"/repos/{ghrequest.fork_fullname}/git/refs/heads"
    sha = None
    r = utils.query_request(query)
    for ref in r.json():
        if ref["ref"].split("/")[-1] == ghrequest.target_repo_branch:
            sha = ref["object"]["sha"]

    query = f"/repos/{ghrequest.fork_fullname}/git/refs"
    ghrequest.new_branch = f"{ghrequest.target_repo_branch}-pep8-patch"
    request_json = {
        "ref": f"refs/heads/{ghrequest.new_branch}",
        "sha": sha,
    }
    r = utils.query_request(query, method='POST', json=request_json)

    if r.status_code > 299:
        ghrequest.error = "Could not create a new branch in the fork"


def autopep8ify(ghrequest, config):
    # Run pycodestyle
    r = utils.query_request(ghrequest.diff_url)

    ## All the python files with additions
    patch = unidiff.PatchSet(r.content.splitlines(), encoding=r.encoding)

    # A dictionary with filename paired with list of new line numbers
    py_files = {}

    for patchset in patch:
        if patchset.target_file[-3:] == '.py':
            py_file = patchset.target_file[1:]
            py_files[py_file] = []
            for hunk in patchset:
                for line in hunk.target_lines():
                    if line.is_added:
                        py_files[py_file].append(line.target_line_no)

    # Ignore errors and warnings specified in the config file
    to_ignore = ",".join(config["pycodestyle"]["ignore"])
    arg_to_ignore = ""
    if len(to_ignore) > 0:
        arg_to_ignore = "--ignore " + to_ignore

    for py_file in py_files:
        filename = py_file[1:]
        query = f"https://raw.githubusercontent.com/{ghrequest.repository}/{ghrequest.sha}/{py_file}"
        r = utils.query_request(query)
        with open("file_to_fix.py", 'w+', encoding=r.encoding) as file_to_fix:
            file_to_fix.write(r.text)

        cmd = f'autopep8 file_to_fix.py {arg_to_ignore}'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        ghrequest.results[filename] = stdout.decode(r.encoding)

        os.remove("file_to_fix.py")


def commit(ghrequest):
    fullname = ghrequest.fork_fullname

    for old_file, new_file in ghrequest.results.items():
        query = f"/repos/{fullname}/contents/{old_file}"
        params = {"ref": ghrequest.new_branch}
        r = utils.query_request(query, params=params)
        sha_blob = r.json().get("sha")
        params["path"] = old_file
        content_code = base64.b64encode(new_file.encode()).decode("utf-8")
        request_json = {
            "path": old_file,
            "message": f"Fix PEP 8 errors in {old_file}",
            "content": content_code,
            "sha": sha_blob,
            "branch": ghrequest.new_branch,
        }
        r = utils.query_request(query, method='PUT', json=request_json)


def create_pr(ghrequest):
    query = f"/repos/{ghrequest.target_repo_fullname}/pulls"
    request_json = {
        "title": "Fix PEP 8 errors",
        "head": f"pep8speaks:{ghrequest.new_branch}",
        "base": ghrequest.target_repo_branch,
        "body": "The changes are suggested by autopep8",
    }
    r = utils.query_request(query, method='POST', json=request_json)
    if r.status_code == 201:
        ghrequest.pr_url = r.json()["html_url"]
    else:
        ghrequest.error = "Pull request could not be created"
