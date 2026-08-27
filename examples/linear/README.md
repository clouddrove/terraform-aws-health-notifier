# aws-health-notifier linear example

Linear only.

Opens a Linear issue per event and closes it by moving the issue to a workflow
state of type `completed`. Priority uses Linear's native integer priority field
rather than a label.

## Usage

```hcl
module "aws_health_notifier" {
  source = "clouddrove/health-notifier/aws"

  notifiers         = "linear"
  linear_team_key   = "OPS"
  linear_secret_arn = "<linear-secret-arn>"
}
```

The secret holds `api_key`. `linear_team_key` is the short team key (the `OPS`
in `OPS-123`); the team and workflow state UUIDs are resolved from it at
runtime, so no UUIDs go in the config.

## Running this example

```bash
terraform init
terraform apply
```

Replace the placeholder secret ARNs and identifiers in `example.tf` first. This
example declares no backend, so its state is local and disposable. For a real
deployment, call the module from your own root with your own backend, as the
Usage block above shows.
