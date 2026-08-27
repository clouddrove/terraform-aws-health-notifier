# aws-health-notifier complete example

all three sinks, with tag enrichment.

One event fans out to Jira, GitHub, and Linear. Each sink is tracked
independently on `(eventArn, sink)`, so dedup and auto-close are per sink and a
partial failure retries only the sink that failed.

## Usage

```hcl
module "aws_health_notifier" {
  source = "clouddrove/health-notifier/aws"

  notifiers = "jira,github,linear"

  jira_project_key  = "OPS"
  github_repo       = "clouddrove/your-repo"
  linear_team_key   = "OPS"

  jira_secret_arn   = "<jira-secret-arn>"
  github_secret_arn = "<github-secret-arn>"
  linear_secret_arn = "<linear-secret-arn>"

  enrich_tags = true
  org_root_id = "r-xxxx"
}
```

Tag enrichment deploys a read-only role to every member account via a
StackSet and reads `tag_keys` from the account each event belongs to. It is
best-effort: if the read fails the ticket is still created, without the tags.

## Running this example

```bash
terraform init
terraform apply
```

Replace the placeholder secret ARNs and identifiers in `example.tf` first. This
example has no backend, so state is local; the deployable root with the S3
backend lives in [`deploy/`](../../deploy).
