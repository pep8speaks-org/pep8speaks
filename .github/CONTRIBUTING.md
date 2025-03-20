# Contributing to PEP 8 Speaks

:sparkles::tada: First off, thanks for taking the time to contribute! :tada::sparkles:

This guide will help you make changes to PEP 8 Speaks. The [GitHub app](https://github.com/apps/pep8-speaks) is a hosted version which is managed by me.
Since the source code is public, you can fork, deploy and use it freely. Read [instructions to deploy a fork](https://github.com/OrkoHunter/pep8speaks/wiki/Instructions-to-deploy-a-fork).


Table of Contents
=================

* [Questions](#questions)
* [Sending a Pull Request](#sending-a-pull-request)
    * [Run local server](#run-local-server)
    * [How to test locally](#how-to-test-locally)
    * [Code style](#code-style)
* [Documentation](#documentation)
* [Testing](#testing)
* [Additional notes](#additional-notes)


## Questions

[Create an issue](https://github.com/OrkoHunter/pep8speaks/issues/new) and I will get back to you as soon as I can!

## Sending a Pull Request

### Run local server

You can use [`uv`](https://docs.astral.sh/uv/) to manage Python versions easily. Use Python 3.9.x for this project.

- Fork the repository.
- Clone your fork.
- Create a new branch.
- Install the requirements.

``` shell
$ uv sync
```

- Start the server

``` shell
$ uv run server.py
```




### How to test locally

``` shell
$ pytest tests/local
```

These tests do not cover all the source files. The branch will get tested on CI when the Pull Request is created.
You can help writing more local unit tests and mock tests. Thanks to [@chinskiy](https://github.com/chinskiy) for bootstrapping the test framework.

### Code style

Please run `flake8` after making your changes to test the coding style.

``` shell
$ flake8
```

Have a look at `setup.cfg` for flake8 configurations.


## Documentation

> A description of how the project works. Feel free to improve this section or create an issue if more needs to be added.

All the requests sent by GitHub are processed in `server.py` in the root of the repository.

`server.py` then decides what is the type of the request and assigns the appropriate handler function located in `pep8speaks/handlers.py`.

`handlers.py` makes the use of `helpers.py`, `models.py`, `utils.py` and other modules inside `pep8speaks/` to decide what to do with the request.

## Testing

All changes made to the source files have to be submitted via Pull Requests. The test workflow is as follows:

- A Pull Request is created on this repository.
- The branch of the PR is then deployed as a review app on Heroku.
  - This process can not be automated for security reasons. Hence, this is done manually by me.
- A test GitHub app called [test-pep8speaks](https://github.com/apps/test-pep8speaks) is already installed on the repository [OrkoHunter/test-pep8speaks](https://github.com/OrkoHunter/test-pep8speaks).
- The Payload URL of the test GitHub app is changed to that of the recently deployed review app on Heroku.
  - This is usually `https://pep8speaks-pr-###-herokuapp.com` where `###` is the PR number.
- CI is to be restarted. This ensures that the tests would use the deployed review app as server.
- We then wait for the sweet green checks! :white_check_mark:

The crucial tests to be run in this process are written inside [tests/test_workflow.py](https://github.com/OrkoHunter/pep8speaks/blob/master/tests/test_workflow.py). The workflow is written in the module and is as follows :

* Each branch on https://github.com/OrkoHunter/test-pep8speaks correspond to a type of test.
* The test functions create a new branch from the existing branches.
* The new branches are then used to create a Pull Request on the master branch of the test repository.
* We then expect [@pep8speaks](https:/github.com/pep8speaks] to make the comment.
* If the comment is not what we expected for if the bot does not comment at all, the test fails.
* Finally, the test closes the PR and deletes the branch.


**Keywords**
head: The new branch which is used to create the Pull Request.
base: The existing branch where the changes are supposed to pulled into.
sha: sha of the latest commit in the corresponding test branches.
     Get the list of sha of the repo at
     https://api.github.com/repos/OrkoHunter/test-pep8speaks/git/refs/heads/



## Additional notes

- The README and this document is inside the `/.github/` directory.
- After editing markdown documents, consider updating the Table of Contents. Check out this cool [script](https://github.com/ekalinin/github-markdown-toc/).
- Check out the following resources to get help.
  - https://guides.github.com/
  - https://help.github.com/en/articles/creating-a-pull-request


Thanks! :heart: :heart: :heart:
