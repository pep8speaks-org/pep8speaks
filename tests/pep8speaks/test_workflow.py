"""
[ ] Create a new PR involving Python files with errors without .pep8speaks.yml
[ ] Create a new PR involving Python files with errors with .pep8speaks.yml
[ ] Create a new PR involving Python files without errors without .pep8speaks.yml
[ ] Create a new PR involving Python files without errors with .pep8speaks.yml
[ ] Create a new PR not involving Python files with errors
[ ] Add a new commit to an opened PR with fixing the issues with .pep8speaks.yml
[ ] Add a new commit to an opened PR with fixing the issues without .pep8speaks.yml
[ ] Add a new commit to an opened PR with maintaining the issues with .pep8speaks.yml
[ ] Add a new commit to an opened PR with maintaining the issues without .pep8speaks.yml
[ ] Add a new commit to an opened PR with creating new issues with .pep8speaks.yml
[ ] Add a new commit to an opened PR with creating new issues without .pep8speaks.yml
"""
import os
import time
import uuid
from pep8speaks.utils import query_request


def create_a_new_pr(repo, expected_comment, head, sha, base="master"):
    # Get the list of sha of the repo at
    # https://api.github.com/repos/OrkoHunter/test-pep8speaks/git/refs/heads/

    print(f"Testing https://github.com/{repo}/tree/{head}")
    print("Waiting is required to to avoid triggering GitHub API abuse")

    responses_ok = []  # Store all GitHub requests r.ok variable and assert at the end. This
                       # will enable debugging the requests

    # Create a new branch from the head branch for a new PR
    new_branch = f"{head}-{uuid.uuid4().hex}"
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
    if os.environ.get("TRAVIS_PULL_REQUEST", False):
        pr_number = os.environ.get("TRAVIS_PULL_REQUEST")
        pr_title = f"Testing PR #{os.environ} on OrkoHunter/PEP8Speaks"
        pr_body = f"Testing https://github.com/OrkoHunter/pep8speaks/pull/{pr_number}\n\n"
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
    """See https://github.com/{repo}/tree/{head}"""
    repo = "OrkoHunter/test-pep8speaks"
    head = "test-errors-without-pep8speaks.yml"
    sha = "7bd64e782f605d3a4f7388c0c993ebb344a952c4"
    pr_number = 81
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
    """See https://github.com/{repo}/tree/{head}"""
    repo = "OrkoHunter/test-pep8speaks"
    head = "test-errors-with-pep8speaks.yml"
    sha = "076c6c107250b61f9bec84230e5c2aa63c337901"
    pr_number = 82
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
    """See https://github.com/{repo}/tree/{head}"""
    repo = "OrkoHunter/test-pep8speaks"
    head = "test-errors-with-setup.cfg-and-pep8speaks.yml"
    sha = "d2dfbb72f2e72758bad016b682e5f9a5a38d5599"
    pr_number = 83
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

if __name__ == "__main__":
    test_errors_with_pep8speaks_yml()
