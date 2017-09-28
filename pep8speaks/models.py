from pep8speaks import utils


class GHRequest(object):
    """A payload object sent by GitHub"""
    def __init__(self, request, event):
        self.OK = self._is_request_valid(request, event)

        # Dictionary with filename matched with corresponding list of results
        self.results = {}

        # Dictionary with filename matched with list of results caused by
        # pycodestyle arguments
        self.extra_results = {}

        # Generic object for the pull request of payload
        self.pull_request = self._get_pull_request(request, event)

        self._set_properties(request, event)

    def _get_pull_request(self, request, event):
        """
        Get data about the pull request created
        """
        if event == "issue_comment":
            pr_url = request.json['issue']['pull_request']['url']
            pull_request = utils._request(pr_url).json()
        elif event in ("pull_request", "pull_request_review"):
            pull_request = request.json['pull_request']
        else:
            return None
        return pull_request

    def _is_request_valid(self, request, event):
        # A valid pull request payload can only be created or updated with commits
        if event == 'pull_request':
            if request.json['action'] in ['synchronize', 'opened', 'reopened']:
                return True
        elif event == 'issue_comment':
            if request.json['action'] in ('created', 'edited') and 'pull_request' in request.json['issue']:
                return True

        return False

    def _set_properties(self, request, event):
        """
        Set necessary properties of the object taken from the data in request.
        """
        self._set_defaults(request)
        self._set_conditionals(request, event)

    def _set_defaults(self, request):
        """
        Set properties common to all event types.
        """
        self.sha = self.pull_request['head']['sha']
        self.action = request.json['action']
        self.author = self.pull_request['user']['login']
        self.pr_desc = self.pull_request['body']
        self.diff_url = self.pull_request['diff_url']
        self.pr_title = self.pull_request['title']
        self.pr_number = self.pull_request['number']
        self.repository = request.json['repository']['full_name']
        self.commits_url = self.pull_request['commits_url']
        self.base_branch = self.pull_request['base']['ref']
        self.after_commit_hash = self.pull_request['head']['sha']

    def _set_conditionals(self, request, event):
        """
        Set properties which are specific to event types.
        """
        if event == 'issue_comment':
            self.reviewer = request.json['comment']['user']['login']
            self.review_url = request.json['comment']['html_url']
            self.comment = request.json['comment']['body']
            self.base_branch = request.json['repository']['default_branch']  # Overrides the default

        if event == 'pull_request_review':
            self.reviewer = request.json['review']['user']['login']
            self.review_url = request.json['review']['html_url']
            self.review_body = request.json['review']['body']
