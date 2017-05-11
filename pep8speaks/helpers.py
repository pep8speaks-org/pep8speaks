# -*- coding: utf-8 -*-

import base64
import collections
import datetime
import hmac
import json
import os
import re
import subprocess
import time

import psycopg2
import requests
import unidiff
import yaml
from flask import abort


def update_users(repository):
    """Update users of the integration in the database"""
    if os.environ.get("OVER_HEROKU", False) is not False:
        # Check if repository exists in database
        query = r"INSERT INTO Users (repository, created_at) VALUES ('{}', now());" \
                "".format(repository)

        try:
            cursor.execute(query)
            conn.commit()
        except psycopg2.IntegrityError:  # If already exists
            conn.rollback()


def follow_user(user):
    """Follow the user of the service"""
    headers = {
        "Authorization": "token " + os.environ["GITHUB_TOKEN"],
        "Content-Length": "0",
    }
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    url = "https://api.github.com/user/following/{}"
    url = url.format(user)
    r = requests.put(url, headers=headers, auth=auth)


def update_dict(base, head):
    """
    Recursively merge or update dict-like objects.
    >>> update({'k1': 1}, {'k1': {'k2': {'k3': 3}}})

    Source : http://stackoverflow.com/a/32357112/4698026
    """
    for key, value in head.items():
        if isinstance(base, collections.Mapping):
            if isinstance(value, collections.Mapping):
                base[key] = update_dict(base.get(key, {}), value)
            else:
                base[key] = head[key]
        else:
            base = {key: head[key]}
    return base


def match_webhook_secret(request):
    """Match the webhook secret sent from GitHub"""
    if os.environ.get("OVER_HEROKU", False) is not False:
        header_signature = request.headers.get('X-Hub-Signature')
        if header_signature is None:
            abort(403)
        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            abort(501)
        mac = hmac.new(os.environ["GITHUB_PAYLOAD_SECRET"].encode(), msg=request.data,
                       digestmod="sha1")
        if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
            abort(403)
    return True


def check_pythonic_pr(data):
    """
    Return True if the PR contains at least one Python file
    """
    files = list(get_files_involved_in_pr(data).keys())
    pythonic = False
    for file in files:
        if file[-3:] == '.py':
            pythonic = True
            break

    return pythonic


def get_config(data):
    """
    Get .pep8speaks.yml config file from the repository and return
    the config dictionary
    """

    # Default configuration parameters
    config = {
        "message": {
            "opened": {
                "header": "",
                "footer": ""
            },
            "updated": {
                "header": "",
                "footer": ""
            }
        },
        "scanner": {"diff_only": False},
        "pycodestyle": {
            "ignore": [],
            "max-line-length": 79,
            "count": False,
            "first": False,
            "show-pep8": False,
            "filename": [],
            "exclude": [],
            "select": [],
            "show-source": False,
            "statistics": False,
            "hang-closing": False,
        },
        "no_blank_comment": True,
        "only_mention_files_with_errors": True,
    }

    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])

    # Configuration file
    url = "https://raw.githubusercontent.com/{}/{}/.pep8speaks.yml"

    url = url.format(data["repository"], data["after_commit_hash"])
    r = requests.get(url, headers=headers, auth=auth)
    if r.status_code == 200:
        try:
            new_config = yaml.load(r.text)
            # overloading the default configuration with the one specified
            config = update_dict(config, new_config)
        except yaml.YAMLError:  # Bad YAML file
            pass

    # Create pycodestyle command line arguments
    arguments = []
    confs = config["pycodestyle"]
    for key, value in confs.items():
        if value:  # Non empty
            if isinstance(value, int):
                if isinstance(value, bool):
                    arguments.append("--{}".format(key))
                else:
                    arguments.append("--{}={}".format(key, value))
            elif isinstance(value, list):
                arguments.append("--{}={}".format(key, ','.join(value)))
    config["pycodestyle_cmd_config"] = ' {arguments}'.format(arguments=' '.join(arguments))

    # pycodestyle is case-sensitive
    config["pycodestyle"]["ignore"] = [e.upper() for e in list(config["pycodestyle"]["ignore"])]

    return config


def get_files_involved_in_pr(data):
    """
    Return a list of file names modified/added in the PR
    """
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    diff_headers = headers.copy()
    diff_headers["Accept"] = "application/vnd.github.VERSION.diff"
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    repository = data["repository"]
    after_commit_hash = data["after_commit_hash"]
    author = data["author"]
    diff_url = "https://api.github.com/repos/{}/pulls/{}"
    diff_url = diff_url.format(repository, str(data["pr_number"]))
    r = requests.get(diff_url, headers=diff_headers, auth=auth)
    patch = unidiff.PatchSet(r.content.splitlines(), encoding=r.encoding)

    files = {}

    for patchset in patch:
        file = patchset.target_file[1:]
        files[file] = []
        for hunk in patchset:
            for line in hunk.target_lines():
                if line.is_added:
                    files[file].append(line.target_line_no)

    return files


def get_python_files_involved_in_pr(data):
    files = get_files_involved_in_pr(data)
    for file in list(files.keys()):
        if file[-3:] != ".py":
            del files[file]

    return files


def run_pycodestyle(data, config):
    """
    Run pycodestyle script on the files and update the data
    dictionary
    """
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    repository = data["repository"]
    after_commit_hash = data["after_commit_hash"]
    author = data["author"]

    # Run pycodestyle
    ## All the python files with additions
    # A dictionary with filename paired with list of new line numbers
    py_files = get_python_files_involved_in_pr(data)

    for file in py_files:
        filename = file[1:]
        url = "https://raw.githubusercontent.com/{}/{}/{}"
        url = url.format(repository, after_commit_hash, file)
        r = requests.get(url, headers=headers, auth=auth)
        with open("file_to_check.py", 'w+', encoding=r.encoding) as file_to_check:
            file_to_check.write(r.text)

        # Use the command line here
        cmd = 'pycodestyle {config[pycodestyle_cmd_config]} file_to_check.py'.format(
            config=config)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        data["extra_results"][filename] = stdout.decode(r.encoding).splitlines()

        # Put only relevant errors in the data["results"] dictionary
        data["results"][filename] = []
        for error in list(data["extra_results"][filename]):
            if re.search("^file_to_check.py:\d+:\d+:\s[WE]\d+\s.*", error):
                data["results"][filename].append(error.replace("file_to_check.py", filename))
                data["extra_results"][filename].remove(error)

        ## Remove errors in case of diff_only = True
        ## which are caused in the whole file
        for error in list(data["results"][filename]):
            if config["scanner"]["diff_only"]:
                if not int(error.split(":")[1]) in py_files[file]:
                    data["results"][filename].remove(error)

        ## Store the link to the file
        url = "https://github.com/{}/blob/{}{}"
        data[filename + "_link"] = url.format(repository, after_commit_hash, file)
        os.remove("file_to_check.py")


def prepare_comment(request, data, config):
    """Construct the string of comment i.e. its header, body and footer"""
    author = data["author"]
    # Write the comment body
    ## Header
    comment_header = ""
    if request.json["action"] == "opened":
        if config["message"]["opened"]["header"] == "":
            comment_header = "Hello @" + author + "! Thanks for submitting the PR.\n\n"
        else:
            comment_header = config["message"]["opened"]["header"] + "\n\n"
    elif request.json["action"] in ["synchronize", "reopened"]:
        if config["message"]["updated"]["header"] == "":
            comment_header = "Hello @" + author + "! Thanks for updating the PR.\n\n"
        else:
            comment_header = config["message"]["updated"]["header"] + "\n\n"

    ## Body
    ERROR = False  # Set to True when any pep8 error exists
    comment_body = []
    for file, issues in data["results"].items():
        if len(issues) == 0:
            if not config["only_mention_files_with_errors"]:
                comment_body.append(
                    " - There are no PEP8 issues in the"
                    " file [`{0}`]({1}) !".format(file, data[file + "_link"]))
        else:
            ERROR = True
            comment_body.append(
                " - In the file [`{0}`]({1}), following "
                "are the PEP8 issues :\n".format(file, data[file + "_link"]))
            for issue in issues:
                ## Replace filename with L
                error_string = issue.replace(file + ":", "Line ")

                ## Link error codes to search query
                error_string_list = error_string.split(" ")
                code = error_string_list[2]
                code_url = "https://duckduckgo.com/?q=pep8%20{0}".format(code)
                error_string_list[2] = "[{0}]({1})".format(code, code_url)

                ## Link line numbers in the file
                line, col = error_string_list[1][:-1].split(":")
                line_url = data[file + "_link"] + "#L" + line
                error_string_list[1] = "[{0}:{1}]({2}):".format(line, col, line_url)
                error_string = " ".join(error_string_list)
                error_string = error_string.replace("Line [", "[Line ")
                comment_body.append("\n> {0}".format(error_string))

        comment_body.append("\n\n")
        if len(data["extra_results"][file]) > 0:
            comment_body.append(" - Complete extra results for this file :\n\n")
            comment_body.append("> " + "".join(data["extra_results"][file]))
            comment_body.append("---\n\n")

    if config["only_mention_files_with_errors"] and not ERROR:
        comment_body.append("Cheers ! There are no PEP8 issues in this Pull Request. :beers: ")


    comment_body = ''.join(comment_body)


    ## Footer
    comment_footer = []
    if request.json["action"] == "opened":
        comment_footer.append(config["message"]["opened"]["footer"])
    elif request.json["action"] in ["synchronize", "reopened"]:
        comment_footer.append(config["message"]["updated"]["footer"])

    comment_footer = ''.join(comment_footer)

    return comment_header, comment_body, comment_footer, ERROR


def comment_permission_check(data, comment):
    """Check for quite and resume status or duplicate comments"""
    PERMITTED_TO_COMMENT = True
    repository = data["repository"]
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])

    # Check for duplicate comment
    url = "https://api.github.com/repos/{}/issues/{}/comments"
    url = url.format(repository, str(data["pr_number"]))
    comments = requests.get(url, headers=headers, auth=auth).json()

    # Get the last comment by the bot
    last_comment = ""
    for old_comment in reversed(comments):
        if old_comment["user"]["id"] == 24736507:  # ID of @pep8speaks
            last_comment = old_comment["body"]
            break

    """
    # Disabling this because only a single comment is made per PR
    text1 = ''.join(BeautifulSoup(markdown(comment)).findAll(text=True))
    text2 = ''.join(BeautifulSoup(markdown(last_comment)).findAll(text=True))
    if text1 == text2.replace("submitting", "updating"):
        PERMITTED_TO_COMMENT = False
    """

    # Check if the bot is asked to keep quiet
    for old_comment in reversed(comments):
        if '@pep8speaks' in old_comment['body']:
            if 'resume' in old_comment['body'].lower():
                break
            elif 'quiet' in old_comment['body'].lower():
                PERMITTED_TO_COMMENT = False


    return PERMITTED_TO_COMMENT


def create_or_update_comment(data, comment):
    comment_mode = None
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])

    query = "https://api.github.com/repos/{}/issues/{}/comments"
    query = query.format(data["repository"], str(data["pr_number"]))
    comments = requests.get(query, headers=headers, auth=auth).json()

    # Get the last comment id by the bot
    last_comment_id = None
    for old_comment in comments:
        if old_comment["user"]["id"] == 24736507:  # ID of @pep8speaks
            last_comment_id = old_comment["id"]
            break

    if last_comment_id is None:  # Create a new comment
        response = requests.post(query, json={"body": comment}, headers=headers, auth=auth)
        data["comment_response"] = response.json()
    else:  # Update the last comment
        utc_time = datetime.datetime.utcnow()
        time_now = utc_time.strftime("%B %d, %Y at %H:%M Hours UTC")
        comment += "\n\n##### Comment last updated on {}"
        comment = comment.format(time_now)

        query = "https://api.github.com/repos/{}/issues/comments/{}"
        query = query.format(data["repository"], str(last_comment_id))
        response = requests.patch(query, json={"body": comment}, headers=headers, auth=auth)


def autopep8(data, config):
    # Run pycodestyle

    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    r = requests.get(data["diff_url"], headers=headers, auth=auth)
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

    for file in py_files:
        filename = file[1:]
        url = "https://raw.githubusercontent.com/{}/{}/{}"
        url = url.format(data["repository"], data["sha"], file)
        r = requests.get(url, headers=headers, auth=auth)
        with open("file_to_fix.py", 'w+', encoding=r.encoding) as file_to_fix:
            file_to_fix.write(r.text)

        cmd = 'autopep8 file_to_fix.py --diff {arg_to_ignore}'.format(
            arg_to_ignore=arg_to_ignore)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        data["diff"][filename] = stdout.decode(r.encoding)

        # Fix the errors
        data["diff"][filename] = data["diff"][filename].replace("file_to_check.py", filename)
        data["diff"][filename] = data["diff"][filename].replace("\\", "\\\\")

        ## Store the link to the file
        url = "https://github.com/{}/blob/{}{}"
        data[filename + "_link"] = url.format(data["repository"], data["sha"], file)
        os.remove("file_to_fix.py")


def create_gist(data, config):
    """Create gists for diff files"""
    REQUEST_JSON = {}
    REQUEST_JSON["public"] = True
    REQUEST_JSON["files"] = {}
    REQUEST_JSON["description"] = "In response to @{0}'s comment : {1}".format(
        data["reviewer"], data["review_url"])

    for file, diffs in data["diff"].items():
        if len(diffs) != 0:
            REQUEST_JSON["files"][file.split("/")[-1] + ".diff"] = {
                "content": diffs
            }

    # Call github api to create the gist
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    url = "https://api.github.com/gists"
    res = requests.post(url, json=REQUEST_JSON, headers=headers, auth=auth).json()
    data["gist_response"] = res
    data["gist_url"] = res["html_url"]


def delete_if_forked(data):
    FORKED = False
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    r = requests.get(url, headers=headers, auth=auth)
    for repo in r.json():
        if repo["description"]:
            if data["target_repo_fullname"] in repo["description"]:
                FORKED = True
                r = requests.delete("https://api.github.com/repos/"
                                "{}".format(repo["full_name"]),
                                headers=headers, auth=auth)
    return FORKED


def fork_for_pr(data):
    FORKED = False
    url = "https://api.github.com/repos/{}/forks"
    url = url.format(data["target_repo_fullname"])
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    r = requests.post(url, headers=headers, auth=auth)
    if r.status_code == 202:
        data["fork_fullname"] = r.json()["full_name"]
        FORKED = True
    else:
        data["error"] = "Unable to fork"
    return FORKED


def update_fork_desc(data):
    # Check if forked (takes time)
    url = "https://api.github.com/repos/{}".format(data["fork_fullname"])
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    r = requests.get(url, headers=headers, auth=auth)
    ATTEMPT = 0
    while(r.status_code != 200):
        time.sleep(5)
        r = requests.get(url, headers=headers, auth=auth)
        ATTEMPT += 1
        if ATTEMPT > 10:
            data["error"] = "Forking is taking more than usual time"
            break

    full_name = data["target_repo_fullname"]
    author, name = full_name.split("/")
    request_json = {
        "name": name,
        "description": "Forked from @{}'s {}".format(author, full_name)
    }
    r = requests.patch(url, data=json.dumps(request_json), headers=headers, auth=auth)
    if r.status_code != 200:
        data["error"] = "Could not update description of the fork"


def create_new_branch(data):
    url = "https://api.github.com/repos/{}/git/refs/heads"
    url = url.format(data["fork_fullname"])
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    sha = None
    r = requests.get(url, headers=headers, auth=auth)
    for ref in r.json():
        if ref["ref"].split("/")[-1] == data["target_repo_branch"]:
            sha = ref["object"]["sha"]

    url = "https://api.github.com/repos/{}/git/refs"
    url = url.format(data["fork_fullname"])
    data["new_branch"] = "{}-pep8-patch".format(data["target_repo_branch"])
    request_json = {
        "ref": "refs/heads/{}".format(data["new_branch"]),
        "sha": sha,
    }
    r = requests.post(url, json=request_json, headers=headers, auth=auth)

    if r.status_code != 200:
        data["error"] = "Could not create new branch in the fork"


def autopep8ify(data, config):
    # Run pycodestyle
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    r = requests.get(data["diff_url"], headers=headers, auth=auth)

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

    for file in py_files:
        filename = file[1:]
        url = "https://raw.githubusercontent.com/{}/{}/{}"
        url = url.format(data["repository"], data["sha"], file)
        r = requests.get(url, headers=headers, auth=auth)
        with open("file_to_fix.py", 'w+', encoding=r.encoding) as file_to_fix:
            file_to_fix.write(r.text)

        cmd = 'autopep8 file_to_fix.py {arg_to_ignore}'.format(
            arg_to_ignore=arg_to_ignore)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        data["results"][filename] = stdout.decode(r.encoding)

        os.remove("file_to_fix.py")


def commit(data):
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])

    fullname = data.get("fork_fullname")

    for file, new_file in data["results"].items():
        url = "https://api.github.com/repos/{}/contents/{}"
        url = url.format(fullname, file)
        params = {"ref": data["new_branch"]}
        r = requests.get(url, params=params, headers=headers, auth=auth)
        sha_blob = r.json().get("sha")
        params["path"] = file
        content_code = base64.b64encode(new_file.encode()).decode("utf-8")
        request_json = {
            "path": file,
            "message": "Fix pep8 errors in {}".format(file),
            "content": content_code,
            "sha": sha_blob,
            "branch": data.get("new_branch"),
        }
        r = requests.put(url, json=request_json, headers=headers, auth=auth)


def create_pr(data):
    headers = {"Authorization": "token " + os.environ["GITHUB_TOKEN"]}
    auth = (os.environ["BOT_USERNAME"], os.environ["BOT_PASSWORD"])
    url = "https://api.github.com/repos/{}/pulls"
    url = url.format(data["target_repo_fullname"])
    request_json = {
        "title": "Fix pep8 errors",
        "head": "pep8speaks:{}".format(data["new_branch"]),
        "base": data["target_repo_branch"],
        "body": "The changes are suggested by autopep8",
    }
    r = requests.post(url, json=request_json, headers=headers, auth=auth)
    if r.status_code == 201:
        data["pr_url"] = r.json()["html_url"]
    else:
        data["error"] = "Pull request could not be created"
