from pep8speaks import utils


class GHRequest(object):
    """A payload object sent by GitHub"""
    def __init__(self, request, event):
        # Keep request body and event type
        self.request = request.json
        self.event = event

        self.OK = self._is_request_valid(self.request, event)

        # Dictionary with filename matched with corresponding list of results
        self.results = {}

        # Dictionary with filename matched with list of results caused by
        # pycodestyle arguments
        self.extra_results = {}

        # In case error occurs in the request
        self.error = None

        # Generic object for the pull request of payload
        self.pull_request = self._get_pull_request(request, event)


        self._set_properties(request, event)

    def _get_pull_request(self, request, event):
        """
        Get data about the pull request created
        """
        if not self.OK:
            return None

        if event == "issue_comment":
            pr_url = request.json['issue']['pull_request']['url']
            pull_request = utils.query_request(pr_url).json()
        elif event == "pull_request":
            pull_request = request.json['pull_request']
        else:
            return None
        return pull_request

    def _is_request_valid(self, request, event):
        # The bot should be able to access the repository
        r = utils.query_request(request['repository']['url'])
        if not r.ok:
            return False

        # A valid pull request payload can only be created or updated with commits
        if event == 'pull_request':
            if request['action'] in ['synchronize', 'opened', 'reopened']:
                return True
        elif event == 'issue_comment':
            if request['action'] in ('created', 'edited') and 'pull_request' in request['issue']:
                return True

        return False

    def _set_properties(self, request, event):
        """
        Set necessary properties of the object taken from the data in request.
        """
        if not self.OK:
            return None

        self._set_defaults(request)
        self._set_conditionals(request, event)

    def _set_defaults(self, request):
        """
        Set properties common to all event types.
        """
        self.sha = self.pull_request['head']['sha']
        self.action = request.json['action']
        self.author = self.pull_request['user']['login']
        self.pr_desc = self.pull_request['body'] if self.pull_request['body'] is not None else ''
        self.diff_url = self.pull_request['diff_url']
        self.pr_title = self.pull_request['title']
        self.pr_number = self.pull_request['number']
        self.repository = request.json['repository']['full_name']
        self.commits_url = self.pull_request['commits_url']
        self.base_branch = self.pull_request['base']['ref']
        self.after_commit_hash = self.pull_request['head']['sha']
        self.private = self.pull_request['base']['repo']['private']

    def _set_conditionals(self, request, event):
        """
        Set properties which are specific to event types.
        """
        if event == 'issue_comment':
            self.reviewer = request.json['comment']['user']['login']
            self.review_url = request.json['comment']['html_url']
            self.comment = request.json['comment']['body']
            self.base_branch = request.json['repository']['default_branch']  # Overrides the default

    def fetch_diff(self):
        """
        Fetch diff and return Response object.
        """
        if self.private:
            # If the target repository is private, fetch diff using API.
            # https://developer.github.com/v3/media/#commits-commit-comparison-and-pull-requests
            print(f'XXX fetch /repos/{self.repository}/pulls/{self.pr_number}  {self.diff_url}')  # fixme
            return utils.query_request(f'/repos/{self.repository}/pulls/{self.pr_number}',
                                       headers={'Accept': 'application/vnd.github.v3.diff'})
        else:
            return utils.query_request(self.diff_url)
