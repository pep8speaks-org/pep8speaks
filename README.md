# pep8speaks
> because it matters.

A GitHub bot which checks pep8 issues and then comments over Pull Requests

<img src="data/readme.png" width="80%">

# How to Use?

 - Go to your project or organization settings
  - GitHub > Settings > Webhooks > Add Webhook
 - Payload URL : https://pep8speaks.herokuapp.com
 - Click on `Let me select individual events.`
 - Tick `Pull request` and untick all other events.
 - Add webhook

# Features

 - To pause the bot from commenting on a PR, comment `@pep8speaks Keep Quiet.`
 - Comment `@pep8speaks Resume now.` to resume.
  - The keywords are `quiet` and `resume` and the mention of the bot.
 - The bot's last comment is not repeated. Hence if the PR is updated and the bot does not comment, it means it stands with its previous comment.

# Configuration
The bot can be configured additionally by adding a `.pep8speaks.yml` file to the base directory of the repo. Here are the available options of the config file :

```yaml
# File : .pep8speaks.yml

message:  # Customize the comment made by the bot
    opened:  # Messages when a new PR is submitted
        header: "Hello @{name}, Thank you for submitting the Pull Request !"
                # The keyword {name} is converted into the author's username
        footer: "Do see the [Hitchhiker's guide to code style](https://goo.gl/hqbW4r)"
                # The messages can be written as they would over GitHub
    updated:  # Messages when new commits are added to the PR
        header: "Hello @{name}, Thank you for updating !"
        footer: ""  # Why to comment the link to the style guide everytime? :)

ignore:  # Errors and warnings to ignore
    - W391  # This comes up if there's a blank line at end of file
    - E203  # You shouldn't be ignoring this. It's for whitespaces before ':'

scanner:
    diff_only: False  # If True, errors caused by only the patch are shown
```

The config file is not required for it to work. The default settings are shown above in the image.

# Contribute

This is a very young project. If you have got any suggestions for new features or improvements, please comment over [here](https://github.com/OrkoHunter/pep8speaks/issues/1). Pull Requests are most welcome !

:heart: