provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = var.name
      ManagedBy = "terraform"
    }
  }
}

# The deployable root. Everything configurable lives on the module; this file
# exists to hold the S3 backend, which Terraform does not allow inside a module.
module "aws_health_notifier" {
  source = "../"

  region      = var.region
  name        = var.name
  environment = var.environment
  label_order = var.label_order
  managedby   = var.managedby
  repository  = var.repository
  tags        = var.tags

  notifiers = var.notifiers

  jira_project_key = var.jira_project_key
  jira_issue_type  = var.jira_issue_type
  jira_secret_arn  = var.jira_secret_arn
  done_transition  = var.done_transition

  github_repo       = var.github_repo
  github_secret_arn = var.github_secret_arn

  linear_team_key   = var.linear_team_key
  linear_secret_arn = var.linear_secret_arn
  linear_done_state = var.linear_done_state

  issue_label      = var.issue_label
  default_priority = var.default_priority
  priority_map     = var.priority_map

  event_type_categories = var.event_type_categories
  log_retention_days    = var.log_retention_days

  enrich_tags        = var.enrich_tags
  describe_role_name = var.describe_role_name
  tag_keys           = var.tag_keys
  org_root_id        = var.org_root_id
}
