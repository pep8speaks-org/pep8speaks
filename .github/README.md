# PEP 8 Speaks [![Build Status](https://travis-ci.org/OrkoHunter/pep8speaks.svg?branch=master)](https://travis-ci.org/OrkoHunter/pep8speaks) ![GitHub release](https://img.shields.io/github/release/OrkoHunter/pep8speaks.svg) ![GitHub contributors](https://img.shields.io/github/contributors/OrkoHunter/pep8speaks.svg) [![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/OrkoHunter) [![Donate on liberapay](https://img.shields.io/liberapay/receives/OrkoHunter.svg?logo=liberapay)](https://liberapay.com/OrkoHunter)


A GitHub :octocat: app to automatically review Python code style over Pull Requests

<p align="center">
    <img src="logo.png">
</p>

Table of Contents
=================

   * [Installation](#installation)
   * [Example](#example)
   * [Main features](#main-features)
   * [Configuration](#configuration)
   * [Popular Users](#popular-users)
   * [Miscellaneous features](#miscellaneous-features)
   * [Private repos](#private-repos)
   * [How to fix PEP 8 issues?](#how-to-fix-pep-8-issues)
   * [Release announcements](#release-announcements)
   * [Contributing](#contributing)

# Installation

 - Go to the homepage of the app - https://github.com/apps/pep8-speaks
 - Click on the Configure button
 - Add repositories or organizations to activate PEP 8 Speaks

# Example

<img src="action.gif">


# Main features

- The bot makes **a single comment on the Pull Request and keeps updating it** on new commits. No hustle on emails !
- The bot **comments only if Python files are involved**. So, install the integration on all of your repositories. The bot would not comment where it should not.
- By default, the bot does not comment if there are no PEP 8 issues. You can change this in configuration.
- **You can use choose between `pycodestyle` or `flake8` as your linter.** The bot can read configurations for both.
- The bot can read your `setup.cfg` for `[flake8]` and `[pycodestyle]` sections. Check out the `Configuration` section below.

# Configuration
**A config file is not required for the integration to work**. However it can be configured additionally by adding a `.pep8speaks.yml` file in the root of the project. Here is an example :

```yaml
# File : .pep8speaks.yml

scanner:
    diff_only: True  # If False, the entire file touched by the Pull Request is scanned for errors. If True, only the diff is scanned.
    linter: pycodestyle  # Other option is flake8

pycodestyle:  # Same as scanner.linter value. Other option is flake8
    max-line-length: 100  # Default is 79 in PEP 8
    ignore:  # Errors and warnings to ignore
        - W504  # line break after binary operator
        - E402  # module level import not at top of file
        - E731  # do not assign a lambda expression, use a def
        - C406  # Unnecessary list literal - rewrite as a dict literal.
        - E741  # ambiguous variable name

no_blank_comment: True  # If True, no comment is made on PR without any errors.
descending_issues_order: False  # If True, PEP 8 issues in message will be displayed in descending order of line numbers in the file

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
- Default settings are in [data/default_pep8speaks.yml](/data/default_pep8speaks.yml). Your `.pep8speaks.yml` will override these values.
- For every Pull Request, the bot looks for `.pep8speaks.yml` in the `base` branch (the existing one). If the file is not found, it then searches the `head` branch (the incoming changes).
- Set the value of `scanner.linter` to either `pycodestyle` or `flake8`
  - flake8 is a wrapper around pycodestyle with additional enforcements.
- For linter configurations (like `ignore` or `max-line-length`), PEP8Speaks will look and prioritize configurations in the following order :
  - `pycodestyle:` or `flake8:` section of `.pep8speaks.yml`.
    - This depends upon the `scanner.linter` value.
  - `[pycodestyle]` or `[flake8]` section of `setup.cfg` file in the root of the project.
    - This is independent of `scanner.linter`. So, `[flake8]` section of `setup.cfg` will also work for pycodestyle.
- Read more on [pycodestyle](http://pycodestyle.pycqa.org/en/latest/) and [flake8](http://flake8.pycqa.org/en/latest/) documentation.

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

Usually, the master branch is deployed as soon as Pull Requests are merged in the repository. However, on every Friday, I  make a release and make sure the latest code is deployed. You do not need to do anything to use the latest version. If you use a fork of PEP 8 Speaks, check out the Release space.

# Contributing

You can support the project by contributing to its development. If you have any suggestions for new features or improvements, please [create an issue](https://github.com/OrkoHunter/pep8speaks/issues/new). Pull Requests are most welcome ! Read [CONTRIBUTING](/.github/CONTRIBUTING.md) doc to understand how the project works and how you can make changes.

The project requires to be hosted on a server and due to which, it needs financial support as well.

Please read the [case for funding PEP 8 Speaks](https://github.com/OrkoHunter/pep8speaks/wiki/Funding).

[![Donate](https://img.shields.io/liberapay/receives/OrkoHunter.svg?logo=liberapay)](https://liberapay.com/OrkoHunter)
[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.me/orkohunter)

If you use this project and you like it, [please let me know](https://saythanks.io/to/OrkoHunter). Thanks!

:heart:

<sub><sup><sub>This project does not endorse all of the rules of the original PEP 8 and thus believes in customizing pycodestyle.

<sub><sup><sub>[.](https://github.com/OrkoHunter/python-easter-eggs)

<h2 align="center">Gold Sponsors</h2>

[Become a Gold Sponsor](https://github.com/OrkoHunter/pep8speaks/wiki/Funding#how-to-donate) and get your logo and name with a link to your site on our README and our [website](https://pep8speaks.com).

<table>
  <tbody>
    <tr>
      <td align="center" valign="top">
        <a href="https://www.python.org/psf/">
          <img width="100" height="184" src="https://wiki.python.org/psf/Logo?action=AttachFile&do=get&target=PSF-vertical-F.png">
          <br><br>
          <p>Python Software Foundation</p>
        </a>
      </td>
      <td align="center" valign="top">
        <a href="https://weblate.org/">
          <img width="184" height="160" src="https://raw.githubusercontent.com/WeblateOrg/graphics/master/logo-formats/Basic-Square.png">
          <br><br>
          <p>Weblate</p>
        </a>
      </td>
    </tr>
</tbody>
</table>


<h2 align="center">Silver Sponsors</h2>

[Become a Silver Sponsor](https://github.com/OrkoHunter/pep8speaks/wiki/Funding#how-to-donate) and get your logo and name with a link to your site on our README and our [website](https://pep8speaks.com).

<table>
  <tbody>
    <tr>
      <td align="center" valign="top">
        <a href="https://ccextractor.org">
          <img width="150" height="150" src="https://raw.githubusercontent.com/CCExtractor/ccextractor-org-media/master/static/ccx_logo_transparent_800x600.png">
          <br><br>
          <p>CCExtractor</p>
        </a>
      </td>
      <td align="center" valign="top">
        <a href="https://github.com/debugger22">
          <img width="150" height="150" src="https://avatars3.githubusercontent.com/u/2821646?s=400&v=4">
          <br><br>
          <p>Sudhanshu Mishra</p>
        </a>
      </td>
    </tr>
</tbody>
</table>
