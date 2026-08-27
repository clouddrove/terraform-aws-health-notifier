provider "aws" {
  region = "us-east-1"
}

# Slack only. Slack is an alerting sink rather than a tracker: there is no
# assignee or status field. Dedup and auto-close still work, because handler
# state is keyed per sink, so a redelivery never reposts.
module "aws_health_notifier" {
  source = "../../"

  name        = "aws-health-notifier"
  environment = "prod"

  notifiers = "slack"

  # A channel id, not a name: names can be changed out from under the config.
  # Find it in the channel's "View channel details" footer.
  slack_channel = "C0123456789"

  # Secret payload:
  #   { "bot_token": "xoxb-..." }
  # The bot needs chat:write and reactions:write, and must be invited to the
  # channel: a bot cannot post to a channel it is not a member of.
  slack_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/slack-XXXX"

  # Slack has no priority field, so priority is rendered as an emoji and a
  # field in the message rather than becoming a label.
  default_priority = "Low"
  priority_map = {
    AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High"
  }

  # issue_label is left at its default: the Slack notifier does not apply it.
}
