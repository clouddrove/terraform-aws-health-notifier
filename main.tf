##-----------------------------------------------------------------------------
## Labels module provides consistent naming and tagging for every resource.
##-----------------------------------------------------------------------------
module "labels" {
  source  = "clouddrove/labels/aws"
  version = "1.3.1"

  name        = var.name
  environment = var.environment
  repository  = var.repository
  managedby   = var.managedby
  label_order = var.label_order
  extra_tags  = var.tags
}

##-----------------------------------------------------------------------------
## Application state. Composite key so each notifier sink is deduped and closed
## independently: a partial failure retries only the sink that failed.
##-----------------------------------------------------------------------------
module "dynamodb" {
  source  = "clouddrove/dynamodb/aws"
  version = "1.0.2"

  name        = "${var.name}-state"
  environment = var.environment
  repository  = var.repository
  managedby   = var.managedby
  label_order = var.label_order

  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "eventArn"
  hash_key_type  = "S"
  range_key      = "sink"
  range_key_type = "S"

  ttl_enabled   = true
  ttl_attribute = "ttl"

  enable_encryption             = true
  enable_point_in_time_recovery = true

  # The module sets read_capacity/write_capacity unconditionally from these
  # (default 5), and AWS rejects both under PAY_PER_REQUEST. null unsets them.
  autoscale_min_read_capacity  = null
  autoscale_min_write_capacity = null
}

##-----------------------------------------------------------------------------
## Dead letter queue for async invocation and EventBridge delivery failures.
##-----------------------------------------------------------------------------
module "sqs" {
  source  = "clouddrove/sqs/aws"
  version = "1.3.1"

  name        = "${var.name}-dlq"
  environment = var.environment
  repository  = var.repository
  managedby   = var.managedby
  label_order = var.label_order

  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

##-----------------------------------------------------------------------------
## Execution role. The policy is built here rather than taken from the lambda
## module, whose built-in policy grants its actions on Resource = "*".
##-----------------------------------------------------------------------------
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid     = "Logs"
    actions = ["logs:CreateLogStream", "logs:PutLogEvents"]
    # Built from the caller's own account and region rather than a wildcard.
    # The group itself is created inside the lambda module, and referencing its
    # output here would make the role depend on the function that consumes it.
    resources = [
      local.log_group_arn,
      "${local.log_group_arn}:*",
    ]
  }
  statement {
    sid       = "Ddb"
    actions   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:Query"]
    resources = [module.dynamodb.table_arn]
  }
  # Emitted only when a sink is configured. An always-present statement would
  # need a placeholder resource, and the only safe placeholder is a wildcard.
  dynamic "statement" {
    for_each = length(local.secret_arns) > 0 ? [1] : []
    content {
      sid       = "Secret"
      actions   = ["secretsmanager:GetSecretValue"]
      resources = local.secret_arns
    }
  }
  statement {
    sid       = "Dlq"
    actions   = ["sqs:SendMessage"]
    resources = [module.sqs.arn]
  }
  statement {
    sid       = "Xray"
    actions   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"]
    resources = ["*"]
  }
  # The describe role is deployed by StackSet to every member account, so the
  # account field must be a wildcard: tag enrichment reads from whichever
  # account the Health event belongs to. The role name is fixed, and the role's
  # own trust policy is what restricts who may assume it.
  # tfsec:ignore:aws-iam-no-policy-wildcards
  statement {
    sid       = "AssumeDescribeRole"
    actions   = ["sts:AssumeRole"]
    resources = ["arn:aws:iam::*:role/${var.describe_role_name}"]
  }
}

module "iam_role" {
  source  = "clouddrove/iam-role/aws"
  version = "1.4.0"

  name        = "${var.name}-role"
  environment = var.environment
  repository  = var.repository
  managedby   = var.managedby
  label_order = var.label_order

  assume_role_policy = data.aws_iam_policy_document.assume.json
  policy             = data.aws_iam_policy_document.lambda.json
  policy_enabled     = true
}

##-----------------------------------------------------------------------------
## Handler. Terraform builds the zip from src/ so the handler/ package dir is
## preserved (entrypoint handler.handler.lambda_handler).
##
## The zip filename carries a hash of the source tree because the upstream
## lambda module sets lifecycle.ignore_changes = [source_code_hash]. With the
## hash ignored, a constant filename would make every code change a silent
## no-op; changing the filename is what forces the function to update.
##-----------------------------------------------------------------------------
locals {
  secret_arns = compact([
    var.jira_secret_arn,
    var.github_secret_arn,
    var.linear_secret_arn,
    var.slack_secret_arn,
  ])

  log_group_arn = "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${module.labels.id}"

  source_files = fileset("${path.module}/src", "**/*.py")
  source_hash  = substr(md5(join("", [for f in local.source_files : filemd5("${path.module}/src/${f}")])), 0, 12)
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/dist/handler-${local.source_hash}.zip"
  excludes    = ["**/__pycache__/**"]
}

module "lambda" {
  source  = "clouddrove/lambda/aws"
  version = "1.3.3"

  name        = var.name
  environment = var.environment
  repository  = var.repository
  managedby   = var.managedby
  label_order = var.label_order

  filename                = data.archive_file.lambda.output_path
  enable_source_code_hash = true
  handler                 = "handler.handler.lambda_handler"
  runtime                 = "python3.13"
  timeout                 = 30
  memory_size             = 256

  reserved_concurrent_executions = var.reserved_concurrent_executions
  tracing_mode                   = "Active"
  dead_letter_target_arn         = module.sqs.arn

  # The scoped role above is used instead of the module's Resource = "*" policy.
  create_iam_role = false
  iam_role_arn    = module.iam_role.arn

  # Log group encryption uses the AWS-managed key: the logs carry only status,
  # eventArn, and ref, never secrets, so a CMK adds cost without benefit.
  enable_kms                        = false
  cloudwatch_logs_retention_in_days = var.log_retention_days

  variables = {
    NOTIFIERS          = var.notifiers
    GITHUB_REPO        = var.github_repo
    JIRA_SECRET_ARN    = var.jira_secret_arn
    GITHUB_SECRET_ARN  = var.github_secret_arn
    LINEAR_SECRET_ARN  = var.linear_secret_arn
    LINEAR_TEAM_KEY    = var.linear_team_key
    LINEAR_DONE_STATE  = var.linear_done_state
    SLACK_SECRET_ARN   = var.slack_secret_arn
    SLACK_CHANNEL      = var.slack_channel
    ISSUE_LABEL        = var.issue_label
    JIRA_PROJECT_KEY   = var.jira_project_key
    JIRA_ISSUE_TYPE    = var.jira_issue_type
    DEFAULT_PRIORITY   = var.default_priority
    PRIORITY_MAP_JSON  = jsonencode(var.priority_map)
    TABLE_NAME         = module.dynamodb.table_name
    DONE_TRANSITION    = var.done_transition
    ENRICH_TAGS        = tostring(var.enrich_tags)
    DESCRIBE_ROLE_NAME = var.describe_role_name
    TAG_KEYS           = var.tag_keys
  }
}

##-----------------------------------------------------------------------------
## EventBridge rule for org-wide AWS Health EC2 events.
##-----------------------------------------------------------------------------
module "eventbridge" {
  source  = "clouddrove/eventbridge/aws"
  version = "1.0.2"

  name        = "${var.name}-rule"
  environment = var.environment
  repository  = var.repository
  label_order = var.label_order

  create_bus  = false
  create_role = false

  rules = {
    health = {
      description = "Capture AWS Health EC2 scheduled-change events."
      event_pattern = jsonencode({
        source      = ["aws.health"]
        detail-type = ["AWS Health Event"]
        detail = {
          service           = ["EC2"]
          eventTypeCategory = var.event_type_categories
        }
      })
    }
  }

  targets = {
    health = [{
      name            = "lambda"
      arn             = module.lambda.arn
      dead_letter_arn = module.sqs.arn
      retry_policy = {
        maximum_retry_attempts       = 2
        maximum_event_age_in_seconds = 3600
      }
    }]
  }
}

##-----------------------------------------------------------------------------
## Invoke permission stays a raw resource: routing it through the lambda module
## would make lambda depend on the rule ARN while eventbridge already depends on
## the function ARN, which is a cycle between the two module calls.
##-----------------------------------------------------------------------------
resource "aws_lambda_permission" "events" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.name
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge.eventbridge_rule_arns["health"]
}

resource "aws_sqs_queue_policy" "dlq" {
  queue_url = module.sqs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = module.sqs.arn
      Condition = { ArnEquals = { "aws:SourceArn" = module.eventbridge.eventbridge_rule_arns["health"] } }
    }]
  })
}
