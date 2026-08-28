<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.10.0 |
| <a name="requirement_archive"></a> [archive](#requirement\_archive) | >= 2.8.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 5.80.0 |

## Providers

| Name | Version |
| ---- | ------- |
| <a name="provider_archive"></a> [archive](#provider\_archive) | 2.8.0 |
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.62.0 |

## Modules

| Name | Source | Version |
| ---- | ------ | ------- |
| <a name="module_dynamodb"></a> [dynamodb](#module\_dynamodb) | clouddrove/dynamodb/aws | 1.0.2 |
| <a name="module_eventbridge"></a> [eventbridge](#module\_eventbridge) | clouddrove/eventbridge/aws | 1.0.2 |
| <a name="module_iam_role"></a> [iam\_role](#module\_iam\_role) | clouddrove/iam-role/aws | 1.4.0 |
| <a name="module_labels"></a> [labels](#module\_labels) | clouddrove/labels/aws | 1.3.1 |
| <a name="module_lambda"></a> [lambda](#module\_lambda) | clouddrove/lambda/aws | 1.3.3 |
| <a name="module_sqs"></a> [sqs](#module\_sqs) | clouddrove/sqs/aws | 1.3.1 |

## Resources

| Name | Type |
| ---- | ---- |
| [aws_cloudformation_stack_set.describe](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudformation_stack_set) | resource |
| [aws_cloudformation_stack_set_instance.describe](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudformation_stack_set_instance) | resource |
| [aws_lambda_permission.events](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_sqs_queue_policy.dlq](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue_policy) | resource |
| [archive_file.lambda](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.assume](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_default_priority"></a> [default\_priority](#input\_default\_priority) | Priority applied when no mapping matches the event type. | `string` | `"Low"` | no |
| <a name="input_describe_role_name"></a> [describe\_role\_name](#input\_describe\_role\_name) | Name of the member-account read role for tag enrichment. | `string` | `"aws-health-notifier-describe"` | no |
| <a name="input_done_transition"></a> [done\_transition](#input\_done\_transition) | Jira transition name used to close a ticket when the event resolves. | `string` | `"Done"` | no |
| <a name="input_enrich_tags"></a> [enrich\_tags](#input\_enrich\_tags) | Enable cross-account instance tag enrichment. | `bool` | `false` | no |
| <a name="input_environment"></a> [environment](#input\_environment) | Deployment environment, applied as a name suffix and a tag. | `string` | `"prod"` | no |
| <a name="input_event_type_categories"></a> [event\_type\_categories](#input\_event\_type\_categories) | AWS Health eventTypeCategory values to capture. | `list(string)` | <pre>[<br/>  "scheduledChange"<br/>]</pre> | no |
| <a name="input_github_repo"></a> [github\_repo](#input\_github\_repo) | owner/repo for the GitHub Issues notifier (used when notifiers includes github). | `string` | `""` | no |
| <a name="input_github_secret_arn"></a> [github\_secret\_arn](#input\_github\_secret\_arn) | ARN of the GitHub token secret (used when notifiers includes github). | `string` | `""` | no |
| <a name="input_issue_label"></a> [issue\_label](#input\_issue\_label) | Label applied to every ticket created by the GitHub and Linear notifiers. Empty disables it. | `string` | `"aws-health"` | no |
| <a name="input_jira_issue_type"></a> [jira\_issue\_type](#input\_jira\_issue\_type) | Jira issue type name. | `string` | `"Task"` | no |
| <a name="input_jira_project_key"></a> [jira\_project\_key](#input\_jira\_project\_key) | Jira project key that tickets are created in. | `string` | `""` | no |
| <a name="input_jira_secret_arn"></a> [jira\_secret\_arn](#input\_jira\_secret\_arn) | ARN of the Jira credentials secret (used when notifiers includes jira). | `string` | `""` | no |
| <a name="input_label_order"></a> [label\_order](#input\_label\_order) | Order the labels module composes resource names in. | `list(any)` | <pre>[<br/>  "name",<br/>  "environment"<br/>]</pre> | no |
| <a name="input_linear_done_state"></a> [linear\_done\_state](#input\_linear\_done\_state) | Name of the Linear completed workflow state used to close an issue. Empty picks the team's first completed state. | `string` | `""` | no |
| <a name="input_linear_secret_arn"></a> [linear\_secret\_arn](#input\_linear\_secret\_arn) | ARN of the Linear API key secret (used when notifiers includes linear). | `string` | `""` | no |
| <a name="input_linear_team_key"></a> [linear\_team\_key](#input\_linear\_team\_key) | Linear team key, e.g. OPS (used when notifiers includes linear). Team and workflow state UUIDs are resolved from it at runtime. | `string` | `""` | no |
| <a name="input_log_retention_days"></a> [log\_retention\_days](#input\_log\_retention\_days) | CloudWatch log retention in days. | `number` | `90` | no |
| <a name="input_managedby"></a> [managedby](#input\_managedby) | Contact applied as the ManagedBy tag. | `string` | `"hello@clouddrove.com"` | no |
| <a name="input_name"></a> [name](#input\_name) | Base name for every resource; combined with environment by the labels module. | `string` | `"aws-health-notifier"` | no |
| <a name="input_notifiers"></a> [notifiers](#input\_notifiers) | Comma-separated notifiers to fan out to (jira, github, linear, slack). | `string` | `"jira"` | no |
| <a name="input_org_root_id"></a> [org\_root\_id](#input\_org\_root\_id) | Organization root or OU id the StackSet deploys the read role to (required when enrich\_tags). | `string` | `""` | no |
| <a name="input_priority_map"></a> [priority\_map](#input\_priority\_map) | Map of AWS Health eventTypeCode to Jira priority name. | `map(string)` | <pre>{<br/>  "AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED": "High"<br/>}</pre> | no |
| <a name="input_region"></a> [region](#input\_region) | AWS region for the deployment. | `string` | `"us-east-1"` | no |
| <a name="input_repository"></a> [repository](#input\_repository) | Source repository URL, applied as a tag. | `string` | `"https://github.com/clouddrove/aws-health-notifier"` | no |
| <a name="input_slack_channel"></a> [slack\_channel](#input\_slack\_channel) | Slack channel id, e.g. C0123456789 (used when notifiers includes slack). An id rather than a name, because names can be changed out from under the config. | `string` | `""` | no |
| <a name="input_slack_secret_arn"></a> [slack\_secret\_arn](#input\_slack\_secret\_arn) | ARN of the Slack bot token secret (used when notifiers includes slack). | `string` | `""` | no |
| <a name="input_tag_keys"></a> [tag\_keys](#input\_tag\_keys) | Comma-separated instance tag keys to include on tickets. | `string` | `"Name,Environment"` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Extra tags merged onto every resource. | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_dlq_arn"></a> [dlq\_arn](#output\_dlq\_arn) | ARN of the dead letter queue. |
| <a name="output_dlq_url"></a> [dlq\_url](#output\_dlq\_url) | URL of the dead letter queue. |
| <a name="output_lambda_arn"></a> [lambda\_arn](#output\_lambda\_arn) | ARN of the handler Lambda function. |
| <a name="output_lambda_name"></a> [lambda\_name](#output\_lambda\_name) | Name of the handler Lambda function. |
| <a name="output_role_arn"></a> [role\_arn](#output\_role\_arn) | ARN of the Lambda execution role. |
| <a name="output_rule_arn"></a> [rule\_arn](#output\_rule\_arn) | ARN of the EventBridge rule capturing AWS Health events. |
| <a name="output_table_name"></a> [table\_name](#output\_table\_name) | Name of the DynamoDB state table. |
<!-- END_TF_DOCS -->