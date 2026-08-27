# GitHub Issues only.
#
#   terraform apply -var-file=examples/github.tfvars

region    = "us-east-1"
notifiers = "github"

github_repo       = "clouddrove/your-repo"
github_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/github-XXXX"

# Secret payload ("api_url" is optional, set it for GitHub Enterprise):
#   { "token": "<github-pat>", "api_url": "https://api.github.com" }
#
# The PAT needs issues read and write on the target repo.

# Label applied to every issue this Lambda opens, created if missing.
# Set to "" to disable.
issue_label = "aws-health"

default_priority = "Low"

# Priority becomes a priority:<level> label on the issue.
priority_map = {
  AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High"
}

event_type_categories = ["scheduledChange"]

# Opt-in instance tag enrichment. Deploys a read-only role to every member
# account via a StackSet, then reads these tags from the event's account.
# enrich_tags = true
# org_root_id = "r-xxxx"
# tag_keys    = "Name,Environment"
