# All three sinks. One AWS Health event fans out to Jira, GitHub, and Linear,
# each tracked independently, so dedup and auto-close are per sink.
#
#   terraform apply -var-file=examples/all.tfvars

region    = "us-east-1"
notifiers = "jira,github,linear"

jira_project_key = "OPS"
github_repo      = "clouddrove/your-repo"
linear_team_key  = "OPS"

jira_secret_arn   = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/jira-XXXX"
github_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/github-XXXX"
linear_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/linear-XXXX"

jira_issue_type = "Task"

# Jira closes via a workflow transition; Linear moves the issue to a completed
# workflow state. Leave linear_done_state unset to use the team's first one.
done_transition = "Done"

# Applied by the GitHub and Linear sinks. Jira ignores it.
issue_label = "aws-health"

default_priority = "Low"

# One map, read differently per sink: a Jira priority name, a priority:<level>
# GitHub label, and Linear's native integer priority.
priority_map = {
  AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High"
}

event_type_categories = ["scheduledChange"]

# Opt-in instance tag enrichment. Deploys a read-only role to every member
# account via a StackSet, then reads these tags from the event's account.
# enrich_tags = true
# org_root_id = "r-xxxx"
# tag_keys    = "Name,Environment"
