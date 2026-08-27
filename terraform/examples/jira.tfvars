# Jira Cloud only.
#
#   terraform apply -var-file=examples/jira.tfvars

region    = "us-east-1"
notifiers = "jira"

jira_project_key = "OPS"
jira_secret_arn  = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/jira-XXXX"

# Secret payload:
#   { "base_url": "https://your-domain.atlassian.net",
#     "email": "automation@your-domain.com",
#     "api_token": "<jira-api-token>" }

jira_issue_type = "Task"

# Transition used to close the ticket when the event resolves. Must exist in
# the project's workflow.
done_transition = "Done"

default_priority = "Low"

priority_map = {
  AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High"
}

event_type_categories = ["scheduledChange"]

# issue_label is deliberately absent: the Jira notifier does not apply it.

# Opt-in instance tag enrichment. Deploys a read-only role to every member
# account via a StackSet, then reads these tags from the event's account.
# enrich_tags = true
# org_root_id = "r-xxxx"
# tag_keys    = "Name,Environment"
