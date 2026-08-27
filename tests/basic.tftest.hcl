# Native `terraform test` coverage for the module.
#
# The AWS provider is mocked so these run plan-only with no credentials and no
# real resources: an unmocked provider calls GetCallerIdentity even for a plan,
# which would make the suite unrunnable in CI without secrets.

mock_provider "aws" {
  # Policy documents are computed by the provider, so the mock returns a
  # placeholder string where the IAM resources require real JSON.
  override_data {
    target = data.aws_iam_policy_document.assume
    values = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  }

  override_data {
    target = data.aws_iam_policy_document.lambda
    values = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  }
}

variables {
  name        = "aws-health-notifier"
  environment = "test"
}

run "validate_module" {
  command = plan
}

run "jira_only" {
  command = plan

  variables {
    notifiers        = "jira"
    jira_project_key = "OPS"
    jira_secret_arn  = "arn:aws:secretsmanager:us-east-1:111122223333:secret:jira-AbCdEf"
  }
}

run "all_sinks" {
  command = plan

  variables {
    notifiers         = "jira,github,linear,slack"
    jira_project_key  = "OPS"
    github_repo       = "clouddrove/example"
    linear_team_key   = "OPS"
    jira_secret_arn   = "arn:aws:secretsmanager:us-east-1:111122223333:secret:jira-AbCdEf"
    github_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:github-AbCdEf"
    linear_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:linear-AbCdEf"
    slack_channel     = "C0123456789"
    slack_secret_arn  = "arn:aws:secretsmanager:us-east-1:111122223333:secret:slack-AbCdEf"
  }
}

run "slack_only" {
  command = plan

  variables {
    notifiers        = "slack"
    slack_channel    = "C0123456789"
    slack_secret_arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:slack-AbCdEf"
  }
}
