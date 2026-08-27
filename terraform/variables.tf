variable "region" {
  description = "AWS region for the deployment."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix applied to all resource names."
  type        = string
  default     = "aws-health-notifier"
}

variable "notifiers" {
  description = "Comma-separated notifiers to fan out to (jira, github, linear)."
  type        = string
  default     = "jira"
}

variable "jira_project_key" {
  description = "Jira project key that tickets are created in."
  type        = string
  default     = ""
}

variable "jira_issue_type" {
  description = "Jira issue type name."
  type        = string
  default     = "Task"
}

variable "default_priority" {
  description = "Priority applied when no mapping matches the event type."
  type        = string
  default     = "Low"
}

variable "priority_map" {
  description = "Map of AWS Health eventTypeCode to Jira priority name."
  type        = map(string)
  default     = { AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED = "High" }
}

variable "done_transition" {
  description = "Jira transition name used to close a ticket when the event resolves."
  type        = string
  default     = "Done"
}

variable "jira_secret_arn" {
  description = "ARN of the Jira credentials secret (used when notifiers includes jira)."
  type        = string
  default     = ""
}

variable "github_secret_arn" {
  description = "ARN of the GitHub token secret (used when notifiers includes github)."
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "owner/repo for the GitHub Issues notifier (used when notifiers includes github)."
  type        = string
  default     = ""
}

variable "linear_secret_arn" {
  description = "ARN of the Linear API key secret (used when notifiers includes linear)."
  type        = string
  default     = ""
}

variable "linear_team_key" {
  description = "Linear team key, e.g. OPS (used when notifiers includes linear). Team and workflow state UUIDs are resolved from it at runtime."
  type        = string
  default     = ""
}

variable "linear_done_state" {
  description = "Name of the Linear completed workflow state used to close an issue. Empty picks the team's first completed state."
  type        = string
  default     = ""
}

variable "issue_label" {
  description = "Label applied to every ticket created by the GitHub and Linear notifiers. Empty disables it."
  type        = string
  default     = "aws-health"
}

variable "event_type_categories" {
  description = "AWS Health eventTypeCategory values to capture."
  type        = list(string)
  default     = ["scheduledChange"]
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 90
}

variable "enrich_tags" {
  description = "Enable cross-account instance tag enrichment."
  type        = bool
  default     = false
}

variable "describe_role_name" {
  description = "Name of the member-account read role for tag enrichment."
  type        = string
  default     = "aws-health-notifier-describe"
}

variable "tag_keys" {
  description = "Comma-separated instance tag keys to include on tickets."
  type        = string
  default     = "Name,Environment"
}

variable "org_root_id" {
  description = "Organization root or OU id the StackSet deploys the read role to (required when enrich_tags)."
  type        = string
  default     = ""
}
