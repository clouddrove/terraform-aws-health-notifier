# aws-health-notifier jira example

Jira only.

Creates a Jira ticket per AWS Health EC2 scheduled event and closes it via the
`done_transition` workflow transition when the event resolves.

## Usage

```hcl
module "aws_health_notifier" {
  source = "clouddrove/health-notifier/aws"

  notifiers        = "jira"
  jira_project_key = "OPS"
  jira_secret_arn  = "<jira-secret-arn>"
}
```

The secret holds `base_url`, `email`, and `api_token`. The Jira account needs
permission to create issues, add comments, and transition issues.

## Running this example

```bash
terraform init
terraform apply
```

Replace the placeholder secret ARNs and identifiers in `example.tf` first. This
example has no backend, so state is local; the deployable root with the S3
backend lives in [`deploy/`](../../deploy).
