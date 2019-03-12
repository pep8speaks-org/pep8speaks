import os
import time
import uuid
from pep8speaks.utils import query_request

"""
**Testing workflow is as follows**
* Each branch on https://github.com/OrkoHunter/test-pep8speaks correspond to a type of test.
* The test functions create a new branch from the existing branches.
* The new branches are then used to create a Pull Request on the master branch of the test repository.
* Meanwhile, the PR responsible to run the tests gets deployed on a test Heroku app.
* @OrkoHunter has to manually update Webhook URL of the test-PEP8Speaks app installed on the test repo. (This can be automated)
* We then expect @pep8speaks to make the comment.
* If the comment is not what we expected for if the bot does not comment at all, the test fails.
* Finally, the test closes the PR and deletes the branch.

**Keywords**
head: The new branch which is used to create the Pull Request.
base: The existing branch where the changes are supposed to pulled into.
sha: sha of the latest commit in the corresponding test branches.
     Get the list of sha of the repo at
     https://api.github.com/repos/OrkoHunter/test-pep8speaks/git/refs/heads/

"""


def create_a_new_pr(repo, expected_comment, head, sha, base="master"):
    """Create a new Pull Request on a test repository and verify the comment by pep8speaks."""

    print(f"Testing https://github.com/{repo}/tree/{head}")
    print("Waiting is required to to avoid triggering GitHub API abuse")

    responses_ok = []  # Store all GitHub requests r.ok variable and assert at the end. This
    # will enable debugging the requests

    # Create a new branch from the head branch for a new PR
    new_branch = f"{uuid.uuid4().hex}-{head}"
    request_json = {
        "ref": f"refs/heads/{new_branch}",
        "sha": sha,
    }
    query = f"/repos/{repo}/git/refs"
    r = query_request(query, method="POST", json=request_json)
    responses_ok.append(r.ok)
    if r.ok:
        print("New branch created!")

    # Create a pull request with the newly created branch and base branch on repo
    TRAVIS_PR_NUMBER = os.environ.get("TRAVIS_PULL_REQUEST", False)
    if TRAVIS_PR_NUMBER:
        pr_title = f"Testing PR #{TRAVIS_PR_NUMBER} on OrkoHunter/PEP8Speaks"
        pr_body = f"Testing https://github.com/OrkoHunter/pep8speaks/pull/{TRAVIS_PR_NUMBER}\n\n"
    else:
        pr_title = "Testing new changes"
        pr_body = "Not triggered by Travis.\n\n"

    pr_body += f"---\n*Expected Result -*\n\n---\n{expected_comment}\n---"

    request_body = {
        'title': pr_title,
        'body': pr_body,
        'base': base,
        'head': new_branch
    }

    query = f"/repos/{repo}/pulls"
    r = query_request(query=query, method="POST", json=request_body)
    responses_ok.append(r.ok)
    response_data = r.json()
    print(response_data)
    test_pr_number = response_data['number']
    print(f"Test PR Number #{test_pr_number}")

    # Wait for @pep8speaks to comment
    time.sleep(20)

    # Get the comment by @pep8speaks
    query = f"/repos/{repo}/issues/{test_pr_number}/comments"
    r = query_request(query=query)
    responses_ok.append(r.ok)
    response_data = r.json()
    print("response_data for comments check ", response_data)
    comment = response_data[0]["body"]

    # Close the pull request
    query = f"/repos/{repo}/pulls/{test_pr_number}"
    r = query_request(query=query, method="PATCH", json={'state': 'closed'})
    responses_ok.append(r.ok)
    print("For closing the PR")
    print(r.content.decode("utf-8"))

    # Delete the branch
    query = f"/repos/{repo}/git/refs/heads/{new_branch}"
    r = query_request(query=query, method="DELETE")
    responses_ok.append(r.ok)

    return responses_ok, comment


def test_errors_without_pep8speaks_yml():
    """This Pull Request introduces PEP 8 errors to a Python file. Errors should be reported here with the default configuration.

    See https://github.com/{repo}/tree/{head}"""
    repo = "OrkoHunter/test-pep8speaks"
    head = "test-errors-without-pep8speaks.yml"
    sha = "7bd64e782f605d3a4f7388c0c993ebb344a952c4"
    expected_comment = (
        "Hello @pep8speaks! Thanks for opening this PR. We checked the lines you've touched for [PEP 8](https://"
        "www.python.org/dev/peps/pep-0008) issues, and found:\n\n* In the file [`modules/good_module.py`](https:/"
        "/github.com/OrkoHunter/test-pep8speaks/blob/7bd64e782f605d3a4f7388c0c993ebb344a952c4/modules/good_module"
        ".py):\n\n> [Line 14:80](https://github.com/OrkoHunter/test-pep8speaks/blob/7bd64e782f605d3a4f7388c0c993e"
        "bb344a952c4/modules/good_module.py#L14): [E501](https://duckduckgo.com/?q=pep8%20E501) line too long (14"
        "7 > 79 characters)\n> [Line 16:5](https://github.com/OrkoHunter/test-pep8speaks/blob/7bd64e782f605d3a4f7"
        "388c0c993ebb344a952c4/modules/good_module.py#L16): [E266](https://duckduckgo.com/?q=pep8%20E266) too man"
        "y leading '#' for block comment\n\n")

    responses, comment = create_a_new_pr(repo, expected_comment, head, sha)
    assert all(responses) is True
    assert comment == expected_comment


def test_errors_with_pep8speaks_yml():
    """This Pull Request introduces PEP 8 errors to a Python file. Errors should be reported here with the .pep8speaks.yml file present in this (head) branch since the base branch does not contain any .pep8speaks.yml

    See https://github.com/{repo}/tree/{head}"""
    repo = "OrkoHunter/test-pep8speaks"
    head = "test-errors-with-pep8speaks.yml"
    sha = "076c6c107250b61f9bec84230e5c2aa63c337901"
    expected_comment = (
        "Hello @pep8speaks! Thanks for opening this PR. We checked the lines you've touched for [PEP 8](https://"
        "www.python.org/dev/peps/pep-0008) issues, and found:\n\n* In the file [`modules/good_module.py`](https:/"
        "/github.com/OrkoHunter/test-pep8speaks/blob/076c6c107250b61f9bec84230e5c2aa63c337901/modules/good_module"
        ".py):\n\n> [Line 14:82](https://github.com/OrkoHunter/test-pep8speaks/blob/076c6c107250b61f9bec84230e5c2"
        "aa63c337901/modules/good_module.py#L14): [E501](https://duckduckgo.com/?q=pep8%20E501) line too long (16"
        "7 > 81 characters)\n> [Line 18:1](https://github.com/OrkoHunter/test-pep8speaks/blob/076c6c107250b61f9be"
        "c84230e5c2aa63c337901/modules/good_module.py#L18): [W293](https://duckduckgo.com/?q=pep8%20W293) blank l"
        "ine contains whitespace\n\n"
    )

    responses, comment = create_a_new_pr(repo, expected_comment, head, sha)
    assert all(responses) is True
    assert comment == expected_comment


def test_errors_with_setup_cfg_and_pep8speaks_yml():
    """This Pull Request introduces PEP 8 errors to a Python file. Errors should be reported here with the .pep8speaks.yml and setup.cfg file present in this (head) branch since the base branch does not contain those files.

    See https://github.com/{repo}/tree/{head}"""
    repo = "OrkoHunter/test-pep8speaks"
    head = "test-errors-with-setup.cfg-and-pep8speaks.yml"
    sha = "d2dfbb72f2e72758bad016b682e5f9a5a38d5599"
    expected_comment = (
        "Hello @pep8speaks! Thanks for opening this PR. We checked the lines you've touched for [PEP 8](https://"
        "www.python.org/dev/peps/pep-0008) issues, and found:\n\n* In the file [`modules/good_module.py`](https:/"
        "/github.com/OrkoHunter/test-pep8speaks/blob/d2dfbb72f2e72758bad016b682e5f9a5a38d5599/modules/good_module"
        ".py):\n\n> [Line 2:1](https://github.com/OrkoHunter/test-pep8speaks/blob/d2dfbb72f2e72758bad016b682e5f9a"
        "5a38d5599/modules/good_module.py#L2): [E265](https://duckduckgo.com/?q=pep8%20E265) block comment should"
        " start with '# '\n> [Line 13:1](https://github.com/OrkoHunter/test-pep8speaks/blob/d2dfbb72f2e72758bad01"
        "6b682e5f9a5a38d5599/modules/good_module.py#L13): [E302](https://duckduckgo.com/?q=pep8%20E302) expected "
        "2 blank lines, found 1\n> [Line 13:11](https://github.com/OrkoHunter/test-pep8speaks/blob/d2dfbb72f2e727"
        "58bad016b682e5f9a5a38d5599/modules/good_module.py#L13): [E203](https://duckduckgo.com/?q=pep8%20E203) wh"
        "itespace before ':'\n> [Line 14:82](https://github.com/OrkoHunter/test-pep8speaks/blob/d2dfbb72f2e72758b"
        "ad016b682e5f9a5a38d5599/modules/good_module.py#L14): [E501](https://duckduckgo.com/?q=pep8%20E501) line "
        "too long (159 > 81 characters)\n> [Line 16:1](https://github.com/OrkoHunter/test-pep8speaks/blob/d2dfbb7"
        "2f2e72758bad016b682e5f9a5a38d5599/modules/good_module.py#L16): [W293](https://duckduckgo.com/?q=pep8%20W"
        "293) blank line contains whitespace\n> [Line 17:5](https://github.com/OrkoHunter/test-pep8speaks/blob/d2"
        "dfbb72f2e72758bad016b682e5f9a5a38d5599/modules/good_module.py#L17): [E266](https://duckduckgo.com/?q=pep"
        "8%20E266) too many leading '#' for block comment\n> [Line 18:1](https://github.com/OrkoHunter/test-pep8s"
        "peaks/blob/d2dfbb72f2e72758bad016b682e5f9a5a38d5599/modules/good_module.py#L18): [W293](https://duckduck"
        "go.com/?q=pep8%20W293) blank line contains whitespace\n> [Line 19:11](https://github.com/OrkoHunter/test"
        "-pep8speaks/blob/d2dfbb72f2e72758bad016b682e5f9a5a38d5599/modules/good_module.py#L19): [E225](https://du"
        "ckduckgo.com/?q=pep8%20E225) missing whitespace around operator\n> [Line 40:1](https://github.com/OrkoHu"
        "nter/test-pep8speaks/blob/d2dfbb72f2e72758bad016b682e5f9a5a38d5599/modules/good_module.py#L40): [E305](h"
        "ttps://duckduckgo.com/?q=pep8%20E305) expected 2 blank lines after class or function definition, found 1"
        "\n\n"
    )

    responses, comment = create_a_new_pr(repo, expected_comment, head, sha)
    assert all(responses) is True
    assert comment == expected_comment


def test_errors_with_flake8():
    """Use flake8 as linter and test its configuration."""

    repo = "OrkoHunter/test-pep8speaks"
    head = "test-errors-with-flake8"
    sha = "b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a"
    expected_comment = (
        "Hello @OrkoHunter! Thanks for opening this PR. We checked the lines you've touched for [PEP 8](https://ww"
        "w.python.org/dev/peps/pep-0008) issues, and found:\n\n* In the file [`modules/good_module.py`](https://git"
        "hub.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a/modules/good_module.py"
        "):\n\n> [Line 2:1](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002daf"
        "d71a/modules/good_module.py#L2): [E265](https://duckduckgo.com/?q=pep8%20E265) block comment should start "
        "with '# '\n> [Line 9:18](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a"
        "002dafd71a/modules/good_module.py#L9): [F821](https://duckduckgo.com/?q=pep8%20F821) undefined name 'htabl"
        "e'\n> [Line 9:44](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd7"
        "1a/modules/good_module.py#L9): [F821](https://duckduckgo.com/?q=pep8%20F821) undefined name 'values'\n> [Li"
        "ne 13:1](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a/module"
        "s/good_module.py#L13): [E302](https://duckduckgo.com/?q=pep8%20E302) expected 2 blank lines, found 1\n> [Li"
        "ne 13:11](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a/modul"
        "es/good_module.py#L13): [E203](https://duckduckgo.com/?q=pep8%20E203) whitespace before ':'\n> [Line 14:83]"
        "(https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a/modules/good_m"
        "odule.py#L14): [E501](https://duckduckgo.com/?q=pep8%20E501) line too long (155 > 82 characters)\n> [Line 1"
        "6:1](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a/modules/go"
        "od_module.py#L16): [W293](https://duckduckgo.com/?q=pep8%20W293) blank line contains whitespace\n> [Line 17"
        ":5](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a/modules/goo"
        "d_module.py#L17): [E266](https://duckduckgo.com/?q=pep8%20E266) too many leading '#' for block comment\n> ["
        "Line 18:1](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a/modu"
        "les/good_module.py#L18): [W293](https://duckduckgo.com/?q=pep8%20W293) blank line contains whitespace\n> [L"
        "ine 19:11](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a/modu"
        "les/good_module.py#L19): [E225](https://duckduckgo.com/?q=pep8%20E225) missing whitespace around operator\n"
        "> [Line 40:1](https://github.com/OrkoHunter/test-pep8speaks/blob/b1ea9ab93d7ed0a357182f4bb4f44a002dafd71a/m"
        "odules/good_module.py#L40): [E305](https://duckduckgo.com/?q=pep8%20E305) expected 2 blank lines after clas"
        "s or function definition, found 1\n\n"
    )

    responses, comment = create_a_new_pr(repo, expected_comment, head, sha)
    assert all(responses) is True
    assert comment == expected_comment
