provider "aws" {
  region = "us-east-1"
}

# GitHub Issues only. Priority becomes a priority:<level> label, and
# issue_label is applied to every issue, both created on the repo if missing.
module "aws_health_notifier" {
  source = "../../"

  name_prefix = "aws-health-notifier"
  notifiers   = "github"

  github_repo = "clouddrove/your-repo"

  # Secret payload ("api_url" is optional, set it for GitHub Enterprise):
  #   { "token": "<github-pat>" }
  # The PAT needs issues read and write on the target repo.
  github_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/github-XXXX"

  issue_label = "aws-health"

  default_priority = "Low"
  priority_map = {
    AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High"
  }
}
