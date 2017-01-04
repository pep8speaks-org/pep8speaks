# -*- coding: utf-8 -*-
from contextlib import contextmanager
import json
import os
import sys
import urllib.parse as urlparse
from flask import Flask, render_template, request, Response
from flask_session import Session
import psycopg2
import pycodestyle
import requests
import unidiff
import yaml


if "OVER_HEROKU" in os.environ:  # For running locally
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


app = Flask(__name__)
sess = Session()


@contextmanager
def redirected(stdout):
    saved_stdout = sys.stdout
    sys.stdout = open(stdout, 'w+')
    yield
    sys.stdout = saved_stdout


def update_users(repository):
    if "OVER_HEROKU" in os.environ:
        global conn, cursor
        # Check if repository exists in database
        query = r"INSERT INTO Users (repository, created_at) VALUES ('{}', now());" \
                "".format(repository)

        try:
            cursor.execute(query)
            conn.commit()
        except psycopg2.IntegrityError:  # If already exists
            conn.rollback()


@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == "POST" and "action" in request.json:

        PERMITTED_TO_COMMENT = True

        if request.json["action"] in ["synchronize", "opened", "reopened"]:
            after_commit_hash = request.json["pull_request"]["head"]["sha"]
            repository = request.json["repository"]["full_name"]
            author = request.json["pull_request"]["user"]["login"]
            diff_url = request.json["pull_request"]["diff_url"]
            update_users(repository)  # Update users of the repository
            data = {
                "after_commit_hash": after_commit_hash,
                "repository": repository,
                "author": author,
                "diff_url": diff_url,
                # Dictionary with filename matched with list of results
                "results": {},
            }

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
            PEP8SPEAK_YML_FOUND = False
            r = requests.get("https://api.github.com/repos/" + repository +
                             "/contents/.pep8speaks.yml")
            if r.status_code == 200:
                PEP8SPEAK_YML_FOUND = True
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

            # personalising the messages
            if "message" in config:
                for act in config["message"]:
                    # can be either "opened" or "updated"
                    for pos in config["message"][act]:
                        # can be either "header" or "footer"
                        msg = config["message"][act][pos]
                        new_msg = msg.replace("{name}", author)
                        config["message"][act][pos] = new_msg

            if PEP8SPEAK_YML_FOUND:
                os.remove(".pep8speaks.yml")

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
                r = requests.get("https://raw.githubusercontent.com/" +
                                 repository + "/" + after_commit_hash +
                                 "/" + file)
                with open("file_to_check.py", 'w+') as file_to_check:
                    file_to_check.write(r.text)
                checker = pycodestyle.Checker('file_to_check.py')
                with redirected(stdout='pycodestyle_result.txt'):
                    checker.check_all()
                with open("pycodestyle_result.txt", "r") as f:
                    data["results"][file] = f.readlines()
                data["results"][file] = [i.replace("file_to_check.py", file)[1:] for i in data["results"][file]]

                ## Remove the errors and warnings to be ignored from config
                ## Also remove other errors in case of diff_only = True

                for error in list(data["results"][file]):
                    if config["scanner"]["diff_only"]:
                        if not int(error.split(":")[1]) in py_files[file]:
                            data["results"][file].remove(error)
                            continue  # To avoid duplicate deletion
                    for to_ignore in config["ignore"]:
                        if to_ignore in error:
                            data["results"][file].remove(error)

                os.remove("file_to_check.py")
                os.remove("pycodestyle_result.txt")

            # Write the comment body
            comment = ""

            ## Header
            if request.json["action"] == "opened":
                if config["message"]["opened"]["header"] == "":
                    comment = "Hello @" + author + "! Thanks for submitting the PR.\n\n"
                else:
                    comment = config["message"]["opened"]["header"] + "\n\n"
            elif request.json["action"] in ["synchronize", "reopened"]:
                if config["message"]["updated"]["header"] == "":
                    comment = "Hello @" + author + "! Thanks for updating the PR.\n\n"
                else:
                    comment = config["message"]["updated"]["header"] + "\n\n"
            ## Body
            for file in list(data["results"].keys()):
                if len(data["results"][file]) == 0:
                    comment += " - There are no PEP8 issues in the file `" + file[1:] + "` !"
                else:
                    comment += " - In the file `" + file[1:] + "`, following\
                     are the PEP8 issues :\n"
                    comment += "```\n"
                    for issue in data["results"][file]:
                        comment += issue
                    comment += "```"
                comment += "\n\n"

            ## Footer
            if request.json["action"] == "opened":
                if config["message"]["opened"]["footer"] == "":
                    comment += ""
                else:
                    comment += config["message"]["opened"]["footer"]
            elif request.json["action"] in ["synchronize", "reopened"]:
                if config["message"]["updated"]["footer"] == "":
                    comment += ""
                else:
                    comment += config["message"]["updated"]["footer"]

            # Do not repeat the comment made on the PR by the bot
            data["pr_number"] = request.json["number"]
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

            # Check if the bot is asked to keep quiet
            for old_comment in reversed(comments):
                if '@pep8speaks' in old_comment['body']:
                    if 'resume' in old_comment['body'].lower():
                        break
                    elif 'quiet' in old_comment['body'].lower():
                        PERMITTED_TO_COMMENT = False

            # Make the comment
            if PERMITTED_TO_COMMENT:
                query = "https://api.github.com/repos/" + repository + "/issues/" + \
                        str(data["pr_number"]) + "/comments?access_token={}".format(
                            os.environ["GITHUB_TOKEN"])
                response = requests.post(query, json={"body": comment}).json()
                data["comment_response"] = response

            js = json.dumps(data)
            return Response(js, status=200, mimetype='application/json')
    else:
        return render_template('index.html')


app.secret_key = os.environ["APP_SECRET_KEY"]
app.config['SESSION_TYPE'] = 'filesystem'

sess.init_app(app)
app.debug = True
# app.run()
