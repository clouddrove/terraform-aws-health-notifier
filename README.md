# aws-health-notifier

Turn AWS Health EC2 scheduled events (maintenance, retirement, reboots) into
tracked tickets, automatically, across an AWS Organization. Jira Cloud, GitHub
Issues, and Linear ship today; the sink is pluggable, so Slack or PagerDuty can
be added later without touching the core.

## Why not the AWS Service Management Connector

The Atlassian connector needs a paid Jira Service Management tier and gives no
enrichment, no dedup, and no auto-close. This talks to the Jira REST API
directly from a small Lambda: it works with any Jira Cloud project, enriches the
ticket, dedups, and closes the ticket when the event resolves. Running cost is
about $0.40/month.

## Architecture

```
Member accounts ──(AWS Health org events)──▶ Central Ops account
                                                │
                             EventBridge rule (aws.health, service=EC2)
                                                │
                                     Lambda (Python 3.13)
                                     ├─ dedup / lifecycle ─▶ DynamoDB (eventArn ▶ ref)
                                     ├─ enrich (event payload only)
                                     ├─ priority map
                                     └─ Notifiers ─▶ Jira REST v3, GitHub Issues,
                                                │         Linear GraphQL
                                                │        (create / comment / close)
                                     async failure ─▶ SQS DLQ
```

The Lambda is sink-agnostic. `NOTIFIERS` is a comma list (e.g. `jira,github,linear`) and
the same event fans out to every listed sink. Each sink is tracked independently
in DynamoDB by `(eventArn, sink)`, so dedup and auto-close are per-sink and a
partial failure retries only the sink that failed. Adding a sink is a new
subpackage under `src/handler/notifiers/` plus one branch in the factory.

Lifecycle, per sink, driven by the Health `statusCode` and DynamoDB state:

| Event state | Sink tracked | Action |
|---|---|---|
| open / upcoming | no | create ticket, store `(eventArn, sink) ▶ ref` |
| open / upcoming | yes | dedup, no new ticket for that sink |
| closed / resolved | yes, still open | comment + close, mark that sink closed |
| closed / resolved | yes, already closed | skip (idempotent) |
| closed / resolved | no | ignore (never created a ticket) |

## Repository layout

```
src/handler/
  handler.py            Lambda entrypoint, sink-agnostic orchestration
  config.py             env-driven configuration
  events.py             parse AWS Health events
  state.py              DynamoDB dedup + lifecycle
  secrets.py            read the notifier secret
  logging.py            structured JSON logging
  notifiers/
    base.py             Notifier protocol + NotifierError
    priority.py         event type to priority mapping
    ticket.py           shared title + markdown body rendering
    __init__.py         build_all(cfg) factory
    jira/               client.py, format.py (ADF), notifier.py
    github/             client.py, format.py (markdown), notifier.py
    linear/             client.py (GraphQL), format.py, resolve.py, notifier.py
main.tf, enrichment.tf  the module, built on clouddrove/{lambda,dynamodb,sqs,
variables.tf, outputs.tf   eventbridge,iam-role,labels}/aws
versions.tf
docs/io.md              generated inputs and outputs
README.yaml             canonical source for the generated README
deploy/                 the applyable root: S3 backend + one module block
examples/               runnable examples: jira, github, linear, complete
tests/
  basic.tftest.hcl      native terraform test (mocked provider, no credentials)
  python/               pytest, moto (AWS), urllib mocking (Jira, GitHub, Linear)
.github/workflows/      ci.yml (checks) and deploy.yml (OIDC apply)
```

## Prerequisites

- A central operations AWS account.
- Terraform >= 1.10, AWS provider ~> 6.57.
- At least one notifier target: a Jira Cloud project (create/comment/transition),
  a GitHub repo with a PAT that has issues read and write, or a Linear workspace
  with a personal API key.
- An S3 bucket for Terraform state (native lockfile, no DynamoDB lock table).

## Setup

### 1. Enable org-wide AWS Health (one time, management account)

```bash
aws organizations register-delegated-administrator \
  --account-id <CENTRAL_OPS_ACCOUNT_ID> \
  --service-principal health.amazonaws.com
```

This is an organization-management action, run once outside Terraform. It makes
member-account EC2 Health events surface on the central account event bus.

### 2. Choose notifiers and create a secret for each (central account)

Set `NOTIFIERS` (Terraform var `notifiers`) to a comma list, e.g. `jira`,
`github`, `linear`, or `jira,github,linear` to send to all three. Each selected
notifier reads its own Secrets Manager secret (`jira_secret_arn`,
`github_secret_arn`, `linear_secret_arn`), so create one secret per notifier you
enable.

**Jira** (include `jira` in `NOTIFIERS`) needs `JIRA_PROJECT_KEY` and a secret
passed as `jira_secret_arn`:

```json
{
  "base_url": "https://your-domain.atlassian.net",
  "email": "automation@your-domain.com",
  "api_token": "<jira-api-token>"
}
```

The Jira account needs permission to create issues, add comments, and
transition issues. Priority becomes the Jira priority name.

**GitHub Issues** (include `github` in `NOTIFIERS`) needs `GITHUB_REPO`
(`owner/repo`) and a secret passed as `github_secret_arn`:

```json
{
  "token": "<github-pat>",
  "api_url": "https://api.github.com"
}
```

`api_url` is optional (set it for GitHub Enterprise). The PAT needs issues read
and write on the target repo. Priority becomes a `priority:<level>` label, which
the notifier creates on the repo if missing.

**Linear** (include `linear` in `NOTIFIERS`) needs `LINEAR_TEAM_KEY` and a secret
passed as `linear_secret_arn`:

```json
{
  "api_key": "<linear-personal-api-key>",
  "api_url": "https://api.linear.app/graphql"
}
```

`api_url` is optional. A personal API key is sent in the `Authorization` header
verbatim, with **no `Bearer` prefix** (Linear reserves that for OAuth tokens).

`linear_team_key` is the short team key, the `OPS` in an issue id like `OPS-123`.
The team UUID and the workflow state used to close an issue are resolved from it
on the first invocation and cached for the life of the execution environment, so
no UUIDs belong in your config. Closing sets the issue to the team's first
workflow state of type `completed`; set `linear_done_state` to a state name if
you want a different one.

Priority maps onto Linear's native priority field rather than a label: `Urgent`
becomes 1, `High` 2, `Medium` 3, `Low` 4, and anything unmapped becomes 0
("no priority").

Linear allows 2,500 requests per user per hour on a personal API key. Each event
costs at most a handful of calls, so only very high event volume comes close.

```bash
aws secretsmanager create-secret \
  --name aws-health-notifier/jira \
  --secret-string file://jira.json
```

Note each returned ARN for `jira_secret_arn` / `github_secret_arn` /
`linear_secret_arn`.

Tickets from the GitHub and Linear sinks also carry a shared `issue_label`
(default `aws-health`), created on demand, so every ticket this Lambda opens can
be filtered as a group. Set `issue_label = ""` to turn it off.

### 3. Deploy

```bash
make package        # builds dist/handler.zip
cd deploy
terraform init \
  -backend-config="bucket=<state-bucket>" \
  -backend-config="key=aws-health-notifier/terraform.tfstate" \
  -backend-config="region=<region>"
terraform apply
```

`deploy/` is the only root with a backend; it holds nothing but the backend and
a single `module` block. Everything configurable lives on the module, listed
under [Configuration](#configuration).

To consume the module from your own root instead:

```hcl
module "aws_health_notifier" {
  source = "github.com/clouddrove/aws-health-notifier"

  notifiers       = "linear"
  linear_team_key = "OPS"

  linear_secret_arn = "<linear-secret-arn>"
}
```

## Examples

Each directory under `examples/` is a runnable root that calls the module. Copy
one, replace the placeholder ARNs and identifiers, then `terraform init &&
terraform apply`.

| Example | Sinks |
|---|---|
| [`examples/jira`](examples/jira) | Jira only |
| [`examples/github`](examples/github) | GitHub Issues only |
| [`examples/linear`](examples/linear) | Linear only |
| [`examples/complete`](examples/complete) | all three, plus tag enrichment |

The examples declare no backend, so their state is local. Use `deploy/` for a
real deployment.

## GitHub Actions

Everything runs in CI, and deploys can run from Actions too.

- **`ci.yml`** (every push and PR): ruff lint + format check, mypy strict,
  pytest, a package-and-import check on the Lambda zip, then terraform fmt,
  validate, tflint, and checkov.
- **`deploy.yml`** (manual, from the Actions tab): assumes an AWS role via GitHub
  OIDC (no static keys) and runs `terraform apply` (Terraform builds the Lambda
  zip via the archive provider).

Configure these repo-level Actions variables for deploy:

| Variable | Purpose |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | IAM role the workflow assumes via OIDC |
| `AWS_REGION` | deployment region |
| `TF_STATE_BUCKET` | S3 bucket holding Terraform state |
| `NOTIFIERS` | optional, comma list of `jira`, `github`, `linear`, defaults to `jira` |
| `JIRA_SECRET_ARN` | ARN of the Jira secret (when notifiers includes jira) |
| `GITHUB_SECRET_ARN` | ARN of the GitHub secret (when notifiers includes github) |
| `LINEAR_SECRET_ARN` | ARN of the Linear secret (when notifiers includes linear) |
| `JIRA_PROJECT_KEY` | Jira project for tickets (when notifiers includes jira) |
| `GITHUB_REPO` | owner/repo for issues (when notifiers includes github) |
| `LINEAR_TEAM_KEY` | Linear team key, e.g. `OPS` (when notifiers includes linear) |

The IAM role's trust policy must allow this repository's OIDC subject
(`token.actions.githubusercontent.com`).

## Configuration

| Env var (Lambda) | Terraform variable | Default |
|---|---|---|
| `NOTIFIERS` | `notifiers` | `jira` |
| `JIRA_SECRET_ARN` | `jira_secret_arn` | `""` (required for jira) |
| `GITHUB_SECRET_ARN` | `github_secret_arn` | `""` (required for github) |
| `GITHUB_REPO` | `github_repo` | `""` (required for github) |
| `LINEAR_SECRET_ARN` | `linear_secret_arn` | `""` (required for linear) |
| `LINEAR_TEAM_KEY` | `linear_team_key` | `""` (required for linear) |
| `LINEAR_DONE_STATE` | `linear_done_state` | `""` (first completed state) |
| `ISSUE_LABEL` | `issue_label` | `aws-health` (github and linear) |
| `JIRA_PROJECT_KEY` | `jira_project_key` | `""` (required for jira) |
| `JIRA_ISSUE_TYPE` | `jira_issue_type` | `Task` |
| `DEFAULT_PRIORITY` | `default_priority` | `Low` |
| `PRIORITY_MAP_JSON` | `priority_map` | retirement ▶ High |
| `DONE_TRANSITION` | `done_transition` | `Done` (jira only) |
| `TABLE_NAME` | (set by Terraform) | - |
| `ENRICH_TAGS` | `enrich_tags` | `false` |
| `DESCRIBE_ROLE_NAME` | `describe_role_name` | `aws-health-notifier-describe` |
| `TAG_KEYS` | `tag_keys` | `Name,Environment` |

## Tag enrichment (optional)

Off by default. When enabled, each ticket also shows the affected instances'
tags (Name, environment, whatever you pick), read from the member account the
event belongs to.

Enable it with:

```hcl
enrich_tags = true
org_root_id = "r-xxxx"   # organization root or OU id
tag_keys    = "Name,Environment"
```

Terraform then deploys a read-only role (`describe_role_name`) to every member
account via a service-managed CloudFormation StackSet. The role trusts only the
central Lambda role and allows only `ec2:DescribeInstances`. Per event, the
Lambda assumes that role in the event's account and reads the tags in `tag_keys`.

Enrichment is best-effort: if the role is missing or the read fails, the ticket
is still created without the tag block. With `enrich_tags = false` there is no
member-account footprint at all.

## Development

```bash
make lint        # ruff + mypy
make test        # pytest (moto + urllib mocking, no AWS or ticket system needed)
make tf-test     # terraform test (mocked AWS provider, no credentials)
make package     # build the Lambda zip
make tf-validate # terraform fmt + tflint + checkov
```

The `Dockerfile` bundles the full dev/CI toolchain. The Lambda itself ships as a
zip, not a container.

## Cost

| Item | Monthly |
|---|---|
| EventBridge (AWS events) | $0 |
| Lambda | ~$0 (free tier) |
| DynamoDB on-demand | ~$0 |
| SQS DLQ | ~$0 |
| Secrets Manager | $0.40 |
| **Total** | **~$0.40** |
