provider "aws" {
  region = "us-east-1"
}

# All three sinks plus tag enrichment. One AWS Health event fans out to Jira,
# GitHub, and Linear, each tracked independently on (eventArn, sink), so dedup
# and auto-close are per sink and a partial failure retries only what failed.
module "aws_health_notifier" {
  source = "../../"

  name_prefix = "aws-health-notifier"
  notifiers   = "jira,github,linear"

  jira_project_key = "OPS"
  jira_issue_type  = "Task"
  done_transition  = "Done"
  jira_secret_arn  = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/jira-XXXX"

  github_repo       = "clouddrove/your-repo"
  github_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/github-XXXX"

  linear_team_key   = "OPS"
  linear_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/linear-XXXX"

  # Applied by the GitHub and Linear sinks. Jira ignores it.
  issue_label = "aws-health"

  # One map, read three ways: a Jira priority name, a priority:<level> GitHub
  # label, and Linear's native integer priority.
  default_priority = "Low"
  priority_map = {
    AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High"
  }

  event_type_categories = ["scheduledChange"]

  # Cross-account instance tag enrichment. Deploys a read-only role to every
  # member account via a StackSet, then reads these tags from the event's
  # account. org_root_id is required when enrich_tags is true.
  enrich_tags = true
  org_root_id = "r-xxxx"
  tag_keys    = "Name,Environment"
}
