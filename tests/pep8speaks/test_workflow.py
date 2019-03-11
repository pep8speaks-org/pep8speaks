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
import time
from pep8speaks.utils import query_request

class TestFlow(object):

    def test_errors_without_pep8speaks_yml(self):
        """See https://github.com/OrkoHunter/test-pep8speaks/pull/81"""
        repo = "OrkoHunter/test-pep8speaks"
        pr_number = 81
        expected_comment = (
            "Hello @OrkoHunter! Thanks for updating this PR. We checked the lines you've touched for [PEP 8](https://"
            "www.python.org/dev/peps/pep-0008) issues, and found:\n\n* In the file [`modules/good_module.py`](https:/"
            "/github.com/OrkoHunter/test-pep8speaks/blob/7bd64e782f605d3a4f7388c0c993ebb344a952c4/modules/good_module"
            ".py):\n\n> [Line 14:80](https://github.com/OrkoHunter/test-pep8speaks/blob/7bd64e782f605d3a4f7388c0c993e"
            "bb344a952c4/modules/good_module.py#L14): [E501](https://duckduckgo.com/?q=pep8%20E501) line too long (14"
            "7 > 79 characters)\n> [Line 16:5](https://github.com/OrkoHunter/test-pep8speaks/blob/7bd64e782f605d3a4f7"
            "388c0c993ebb344a952c4/modules/good_module.py#L16): [E266](https://duckduckgo.com/?q=pep8%20E266) too man"
            "y leading '#' for block comment\n\n")

        print(f"Testing https://github.com/{repo}/pull/{pr_number}")

        # Assuming only one comment is made and that too by @pep8speaks
        query = f"/repos/{repo}/issues/{pr_number}/comments"
        r = query_request(query=query)
        assert r.ok == True
        response_data = r.json()
        assert len(response_data) == 1
        assert response_data[0]['user']['login'] == 'pep8speaks'
        comment_id =  response_data[0]['id']

        # Delete the existing comment by @pep8speaks
        query = f"/repos/{repo}/issues/comments/{comment_id}"
        print(query)
        r = query_request(query=query, method="DELETE")
        print(r.content)
        assert r.ok == True

        # Close the pull request
        query = f"/repos/{repo}/pulls/{pr_number}"
        r = query_request(query=query, method="PATCH", json={'state': 'closed'})
        assert r.ok == True

        # Reopen the pull request
        query = f"/repos/{repo}/pulls/{pr_number}"
        r = query_request(query=query, method="PATCH", json={'state': 'open'})
        assert r.ok == True

        # Now wait for 10 seconds for pep8speaks to comment
        time.sleep(10)
        # Verify the comment
        query = f"/repos/{repo}/issues/{pr_number}/comments"
        r = query_request(query=query)
        assert r.ok == True
        print(r.content)
        print(r.reason)
        response_data = r.json()
        assert len(response_data) == 1
        assert response_data[0]['user']['login'] == 'pep8speaks'
        assert response_data[0]["body"] == expected_comment
