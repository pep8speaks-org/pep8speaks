# -*- coding: utf-8 -*-
from contextlib import contextmanager
import hmac
import os
import sys
from flask import abort
import psycopg2
import pycodestyle
import requests
import unidiff
import yaml


@contextmanager
def redirected(stdout):
    saved_stdout = sys.stdout
    sys.stdout = open(stdout, 'w+')
    yield
    sys.stdout = saved_stdout


def update_users(repository):
    if "OVER_HEROKU" in os.environ:
        # Check if repository exists in database
        query = r"INSERT INTO Users (repository, created_at) VALUES ('{}', now());" \
                "".format(repository)

        try:
            cursor.execute(query)
            conn.commit()
        except psycopg2.IntegrityError:  # If already exists
            conn.rollback()


def match_webhook_secret(request):
    if "OVER_HEROKU" in os.environ:
        header_signature = request.headers.get('X-Hub-Signature')
        if header_signature is None:
            abort(403)
        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            abort(501)
        mac = hmac.new(str(secret), msg=request.data, digestmod=sha1)
        if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
            abort(403)
    return True


def get_config(repository):
    PEP8SPEAKS_YML_FOUND = False

    # Default configuration parameters
    config = {
                "ignore": [],
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
                "scanner": {"diff_only": False}
            }

    # Configuration file
    r = requests.get("https://api.github.com/repos/{0}/contents/.pep8speaks.yml"
                     "?access_token={1}".format(repository, os.environ["GITHUB_TOKEN"]))
    if r.status_code == 200:
        PEP8SPEAKS_YML_FOUND = True
        res = requests.get(r.json()["download_url"])
        with open(".pep8speaks.yml", "w+") as config_file:
            config_file.write(res.text)
    # Handle the case of no configuration file resulting in a 404 response code

    # Update default config with those provided
    with open(".pep8speaks.yml", "r") as stream:
        try:
            new_config = yaml.load(stream)
            # overloading the default configuration with the one specified
            for key in new_config:
                config[key] = new_config[key]

        except yaml.YAMLError as e:  # Bad YAML file
            pass

    if PEP8SPEAKS_YML_FOUND:
        os.remove(".pep8speaks.yml")

    return config


def run_pycodestyle(data, config):
    diff_url = data["diff_url"]
    repository = data["repository"]
    after_commit_hash = data["after_commit_hash"]
    author = data["author"]
    # Run pycodestyle
    r = requests.get(diff_url)
    with open(".diff", "w+") as diff_file:
        diff_file.write(r.text)
    ## All the python files with additions
    patch = unidiff.PatchSet.from_filename('.diff', encoding='utf-8')

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

    os.remove('.diff')

    for file in py_files.keys():
        filename = file[1:]
        r = requests.get("https://raw.githubusercontent.com/" +
                         repository + "/" + after_commit_hash +
                         "/" + file)
        with open("file_to_check.py", 'w+') as file_to_check:
            file_to_check.write(r.text)
        checker = pycodestyle.Checker('file_to_check.py')
        with redirected(stdout='pycodestyle_result.txt'):
            checker.check_all()
        with open("pycodestyle_result.txt", "r") as f:
            data["results"][filename] = f.readlines()
        data["results"][filename] = [i.replace("file_to_check.py", filename) for i in data["results"][filename]]

        ## Remove the errors and warnings to be ignored from config
        ## Also remove other errors in case of diff_only = True

        for error in list(data["results"][filename]):
            if config["scanner"]["diff_only"]:
                if not int(error.split(":")[1]) in py_files[file]:
                    data["results"][filename].remove(error)
                    continue  # To avoid duplicate deletion
            for to_ignore in config["ignore"]:
                if to_ignore in error:
                    data["results"][filename].remove(error)

        ## Store the link to the file
        url = "https://github.com/" + author + "/" + \
              repository.split("/")[-1] + "/blob/" + \
              after_commit_hash + file
        data[filename + "_link"] = url

        os.remove("file_to_check.py")
        os.remove("pycodestyle_result.txt")


def prepare_comment(request, data, config):
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
    comment_body = ""
    for file in list(data["results"].keys()):
        if len(data["results"][file]) == 0:
            comment_body += " - There are no PEP8 issues in the" + \
                            " file [`{0}`]({1}) !".format(file, data[file + "_link"])
        else:
            comment_body += " - In the file [`{0}`]({1}), following\
             are the PEP8 issues :\n".format(file, data[file + "_link"])
            for issue in data["results"][file]:
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

                comment_body += "> {0}".format(error_string)
        comment_body += "\n\n"

    ## Footer
    comment_footer = ""
    if request.json["action"] == "opened":
        if config["message"]["opened"]["footer"] == "":
            comment_footer += ""
        else:
            comment_footer += config["message"]["opened"]["footer"]
    elif request.json["action"] in ["synchronize", "reopened"]:
        if config["message"]["updated"]["footer"] == "":
            comment_footer += ""
        else:
            comment_footer += config["message"]["updated"]["footer"]

    return comment_header, comment_body, comment_footer


def comment_permission_check(data, comment):
    PERMITTED_TO_COMMENT = True
    repository = data["repository"]

    # Check for duplicate comment
    query = "https://api.github.com/repos/" + repository + "/issues/" + \
            str(data["pr_number"]) + \
            "/comments?access_token={}".format(os.environ["GITHUB_TOKEN"])
    comments = requests.get(query).json()
    last_comment = ""
    for old_comment in reversed(comments):
        if old_comment["user"]["id"] == 24736507:  # ID of @pep8speaks
            last_comment = old_comment["body"]
            break
    if comment == last_comment:
        PERMITTED_TO_COMMENT = False

    ## Do not comment on updating if no errors were introduced previously
    if "following" not in comment.lower():  # `following are the pep8 issues`
        if "no PEP8 issues" in last_comment:
            if "following" not in last_comment.lower():
                PERMITTED_TO_COMMENT = False  # When both comment have no errors

    # Check if the bot is asked to keep quiet
    for old_comment in reversed(comments):
        if '@pep8speaks' in old_comment['body']:
            if 'resume' in old_comment['body'].lower():
                break
            elif 'quiet' in old_comment['body'].lower():
                PERMITTED_TO_COMMENT = False


    return PERMITTED_TO_COMMENT
