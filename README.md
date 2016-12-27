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
                # The messages can be written as they would on GitHub.
    updated:  # Messages when new commits are added to the PR
        header: "Hello @{name}, Thank you for updating !"
        footer: ""  # Why to comment the link to style guide everytime? :)

ignore:  # Errors and warnings to ignore
    - W391  # This comes up if there's a blank line at end of file
    - E203  # You shouldn't be ignoring this. It's for whitespaces before ':'
```
