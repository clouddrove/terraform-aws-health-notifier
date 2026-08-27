provider "aws" {
  region = "us-east-1"
}

# Linear only. Priority maps onto Linear's native integer priority field
# (Urgent 1, High 2, Medium 3, Low 4, anything else 0) rather than a label.
module "aws_health_notifier" {
  source = "../../"

  name        = "aws-health-notifier"
  environment = "prod"
  notifiers   = "linear"

  # The short team key, the OPS in an issue id like OPS-123. The team UUID and
  # the workflow state used to close an issue are resolved from it at runtime,
  # so no UUIDs belong here.
  linear_team_key = "OPS"

  # Secret payload ("api_url" is optional):
  #   { "api_key": "<linear-personal-api-key>" }
  # The key is sent in the Authorization header verbatim, with no Bearer
  # prefix; Linear reserves that for OAuth tokens.
  linear_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/linear-XXXX"

  # Closing moves the issue to the team's first workflow state of type
  # "completed". Set this only to pick a different one by name.
  # linear_done_state = "Shipped"

  issue_label = "aws-health"

  default_priority = "Low"
  priority_map = {
    AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High"
  }
}
