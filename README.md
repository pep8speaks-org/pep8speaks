# PEP 8 Speaks [![Build Status](https://travis-ci.org/OrkoHunter/pep8speaks.svg?branch=master)](https://travis-ci.org/OrkoHunter/pep8speaks) ![GitHub contributors](https://img.shields.io/github/contributors/OrkoHunter/pep8speaks.svg) [![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/OrkoHunter)

A GitHub :octocat: app to automatically review Python code style over Pull Requests

<h1 align="center"><img src="data/logo.png"></h1>

> "PEP 8 unto thyself, not unto others" - Raymond Hettinger

# Example

<img src="data/action.gif">

# How to Use?

 - Go to the homepage of the app - https://github.com/apps/pep8-speaks
 - Click on the Configure button
 - Add repositories or organizations to activate PEP8Speaks

# Main features

- The bot makes **a single comment on the Pull Request and keeps updating it** on new commits. No hustle on emails !
- The bot **comments only if Python files are involved**. So, install the integration on all of your repositories. The bot would not comment where it should not.
- By default, the bot does not comment if there are no PEP 8 issues. You can change this in configuration.
- The bot can read `setup.cfg` for `[flake8]` or `[pycodestyle]` section for PEP 8 customization. Check out the `Configuration` section below.

# Configuration
**A config file is not required for the integration to work**. However it can be configured additionally by adding a `.pep8speaks.yml` file in the root of the project. Here is an example :

```yaml
# File : .pep8speaks.yml

pycodestyle:
    max-line-length: 100  # Default is 79 in PEP 8
    ignore:  # Errors and warnings to ignore
        - W391
        - E203
        - W504

scanner:
    diff_only: True  # If False, the entire file touched by the Pull Request is scanned for errors. If True, only the diff is scanned.

no_blank_comment: True  # If True, no comment is made on PR without any errors.
descending_issues_order: False  # If True, PEP 8 issues in message will be displayed in descending order of line numbers in the file
only_mention_files_with_errors: True  # If False, a separate status section for each file is made in the comment.

message:  # Customize the comment made by the bot
    opened:  # Messages when a new PR is submitted
        header: "Hello @{name}! Thanks for opening this PR. "
                # The keyword {name} is converted into the author's username
        footer: "Do see the [Hitchhiker's guide to code style](https://goo.gl/hqbW4r)"
                # The messages can be written as they would over GitHub
    updated:  # Messages when new commits are added to the PR
        header: "Hello @{name}! Thanks for updating this PR. "
        footer: ""  # Why to comment the link to the style guide everytime? :)
    no_errors: "There are currently no PEP 8 issues detected in this Pull Request. Cheers! :beers: "
```

**Notes:**
- Default settings are in [data/default_config.json](data/default_config.json). Your `.pep8speaks.yml` will override these values.
- For every Pull Request, the bot looks for `.pep8speaks.yml` in the `base` branch (the existing one). If the file is not found, it then searches the `head` branch (the incoming changes).
- For pycodestyle/flake8 configurations (like `ignore` or `max-line-length`), PEP8Speaks will look and prioritize configurations in the following order :
  - `pycodestyle:` section of `.pep8speaks.yml`
  - `[pycodestyle]` or `[flake8]` section of `setup.cfg` file in the root of the project.
- Read more about the [pycodestyle options](https://pycodestyle.readthedocs.io/en/latest/intro.html#example-usage-and-output)

# Popular Users

<table>
  <tbody>
    <tr>
      <td align="center" valign="top">
        <img src="https://avatars1.githubusercontent.com/u/21206976?v=4&s=200" height="100px">
        <br>
        <a style="text-decoration: none; color: black;" target="_blank" href="https://github.com/pandas-dev/pandas">Pandas</a>
      </td>
      <td align="center" valign="top">
        <img src="https://github.com/sunpy/sunpy-logo/blob/master/generated/sunpy_icon.png?raw=true" height="100px">
        <br>
        <a style="text-decoration: none; color: black" target="_blank" href="https://github.com/sunpy">SunPy</a>
      </td>
      <td align="center" width="20%" valign="top">
        <img src="https://avatars0.githubusercontent.com/u/847984?v=3&s=200" height="100px">
        <br>
        <a style="text-decoration: none; color: black" target="_blank" href="https://github.com/astropy">Astropy</a>
      </td>
      <td align="center" valign="top">
        <img src="https://avatars3.githubusercontent.com/u/17349883?v=3&s=200" height="100px">
        <br>
        <a style="text-decoration: none; color: black" target="_blank" href="https://github.com/scikit-learn-contrib">Scikit Learn Contrib</a>
      </td>
      <td align="center" valign="top">
        <img style="margin-right: 5%" src="https://avatars3.githubusercontent.com/u/897180?v=3&s=400" height="100px">
        <br>
        <a style="text-decoration: none; color: black;" target="_blank" href="https://github.com/scikit-image">Scikit Image</a>
      </td>
      <td align="center" valign="top">
        <img style="margin-right: 5%" src="https://avatars0.githubusercontent.com/u/1284937?v=4&s=200" height="100px">
        <br>
        <a style="text-decoration: none; color: black;" target="_blank" href="https://github.com/spyder-ide/spyder">Spyder IDE</a>
      </td>
     </tr>
  </tbody>
</table>

See the [complete list of organizations and users](https://github.com/OrkoHunter/pep8speaks/wiki/List-of-users-and-orgs).

# Miscellaneous features

 - Comment `@pep8speaks suggest diff` in a comment of the PR, and it will comment a gist of diff suggesting fixes for the PR. [Example](https://github.com/OrkoHunter/test-pep8speaks/pull/22#issuecomment-270826241)
 - Comment `@pep8speaks pep8ify` on the PR and it will create a Pull Request with changes suggested by [`autopep8`](https://github.com/hhatto/autopep8) against the branch of the author of the PR. `autopep8` fixes most of the errors reported by [`pycodestyle`](https://github.com/PyCQA/pycodestyle).
- Add `[skip pep8]` anywhere in the commit message, PR title or PR description to prohibit pep8speaks from commenting on the Pull Request.

# Private repos

This app will only work for publicly hosted repositories. So if you are looking to deploy a fork or **use the app for private repositories**, [here are the instructions](https://github.com/OrkoHunter/pep8speaks/wiki/Instructions-to-deploy-a-fork).

# How to fix PEP 8 issues?

 - Check the errors locally by the command line tool [pycodestyle](https://github.com/PyCQA/pycodestyle) (previously known as `pep8`).
 - [autopep8](https://github.com/hhatto/autopep8) is another command line tool to fix the issues.
 - Also, see [black](https://github.com/ambv/black)

# Release announcements

Updates to the app are announced using the GitHub Release feature over [here](https://github.com/OrkoHunter/pep8speaks/releases). A lot of major changes are made as the community grows bigger. Click on `Watch` -> `Releases only` on top of the page, to get notified about new configurations or feature updates.

# Contribute

If you have any suggestions for new features or improvements, please [create an issue](https://github.com/OrkoHunter/pep8speaks/issues/new). Pull Requests are most welcome ! Also, if you use this project and you like it, [please let me know](https://saythanks.io/to/OrkoHunter) :)

:heart:

<sub><sup><sub>This project does not endorse all of the rules of the original PEP 8 and thus believes in customizing pycodestyle.

<sub><sup><sub>[.](https://github.com/OrkoHunter/python-easter-eggs)
