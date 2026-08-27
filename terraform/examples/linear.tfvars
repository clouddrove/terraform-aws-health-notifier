# Linear only.
#
#   terraform apply -var-file=examples/linear.tfvars

region    = "us-east-1"
notifiers = "linear"

# The short team key, the OPS in an issue id like OPS-123. The team UUID and
# the workflow state used to close an issue are resolved from it at runtime,
# so no UUIDs belong in this file.
linear_team_key   = "OPS"
linear_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:aws-health-notifier/linear-XXXX"

# Secret payload ("api_url" is optional):
#   { "api_key": "<linear-personal-api-key>" }
#
# A personal API key is sent in the Authorization header verbatim, with no
# Bearer prefix; Linear reserves that for OAuth tokens.

# Label applied to every issue this Lambda opens, created if missing.
# Set to "" to disable.
issue_label = "aws-health"

default_priority = "Low"

# Priority maps onto Linear's native priority field, not a label:
# Urgent -> 1, High -> 2, Medium -> 3, Low -> 4, anything else -> 0.
priority_map = {
  AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High"
}

# Closing moves the issue to the team's first workflow state of type
# "completed". Set this only to pick a different one by name.
# linear_done_state = "Shipped"

event_type_categories = ["scheduledChange"]

# Opt-in instance tag enrichment. Deploys a read-only role to every member
# account via a StackSet, then reads these tags from the event's account.
# enrich_tags = true
# org_root_id = "r-xxxx"
# tag_keys    = "Name,Environment"
