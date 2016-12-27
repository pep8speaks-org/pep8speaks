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

# Upcoming features
 - [ ] Create `.pep8speaks.yml` in root directory for more configurations.
 - [ ] Specify warnings to ignore
 - [ ] Customized header and footer message