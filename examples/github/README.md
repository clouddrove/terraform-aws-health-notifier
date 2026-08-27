# aws-health-notifier github example

GitHub Issues only.

Opens a GitHub issue per event, labelled with both `issue_label` and a
`priority:<level>` label. Both labels are created on the repo if missing.

## Usage

```hcl
module "aws_health_notifier" {
  source = "clouddrove/health-notifier/aws"

  notifiers         = "github"
  github_repo       = "clouddrove/your-repo"
  github_secret_arn = "<github-secret-arn>"
}
```

The secret holds `token`, and optionally `api_url` for GitHub Enterprise. The
PAT needs issues read and write on the target repo.

## Running this example

```bash
terraform init
terraform apply
```

Replace the placeholder secret ARNs and identifiers in `example.tf` first. This
example has no backend, so state is local; the deployable root with the S3
backend lives in [`deploy/`](../../deploy).
