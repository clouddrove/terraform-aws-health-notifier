provider "aws" {
  region = "us-east-1"
}

# Jira Cloud only. Tickets are created in JIRA_PROJECT_KEY and closed by the
# named workflow transition when the AWS Health event resolves.
module "aws_health_notifier" {
  source = "../../"

  name        = "aws-health-notifier"
  environment = "prod"
  notifiers   = "jira"

  jira_project_key = "OPS"
  jira_issue_type  = "Task"
  done_transition  = "Done"

  # Secret payload:
  #   { "base_url": "https://your-domain.atlassian.net",
  #     "email": "automation@your-domain.com",
  #     "api_token": "<jira-api-token>" }
  jira_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/jira-XXXX"

  default_priority = "Low"
  priority_map = {
    AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High"
  }

  # issue_label is left at its default because the Jira notifier does not apply it.
}
