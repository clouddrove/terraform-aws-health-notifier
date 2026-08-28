# aws-health-notifier slack example

Slack only.

Posts one message per AWS Health event to a channel, replies in-thread when the
event resolves, and marks the original with a ✅ reaction.

Slack is an alerting sink rather than a tracker: no assignee, no status field,
no audit trail. It complements the ticket sinks rather than replacing one.

## Usage

```hcl
module "aws_health_notifier" {
  source  = "clouddrove/health-notifier/aws"

  notifiers        = "slack"
  slack_channel    = "C0123456789"
  slack_secret_arn = "<slack-secret-arn>"
}
```

The secret holds `bot_token`. The bot needs the `chat:write` and
`reactions:write` scopes, and **must be invited to the channel** — a bot cannot
post to a channel it is not a member of.

`slack_channel` is a channel **id**, not a name, because a channel can be
renamed out from under the configuration. Find it in the channel's "View
channel details" footer.

Resolution is marked with a reaction rather than by editing the message: the
close path receives only the stored reference, not the original event, so an
edit would overwrite the message body with less information than it had.

## Running this example

```bash
terraform init
terraform apply
```

Replace the placeholder secret ARN and channel id in `example.tf` first. This
example declares no backend, so its state is local and disposable. For a real
deployment, call the module from your own root with your own backend, as the
Usage block above shows.
