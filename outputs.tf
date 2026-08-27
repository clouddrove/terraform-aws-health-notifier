output "lambda_name" {
  description = "Name of the handler Lambda function."
  value       = module.lambda.name
}

output "lambda_arn" {
  description = "ARN of the handler Lambda function."
  value       = module.lambda.arn
}

output "rule_arn" {
  description = "ARN of the EventBridge rule capturing AWS Health events."
  value       = module.eventbridge.eventbridge_rule_arns["health"]
}

output "dlq_url" {
  description = "URL of the dead letter queue."
  value       = module.sqs.id
}

output "dlq_arn" {
  description = "ARN of the dead letter queue."
  value       = module.sqs.arn
}

output "table_name" {
  description = "Name of the DynamoDB state table."
  value       = module.dynamodb.table_name
}

output "role_arn" {
  description = "ARN of the Lambda execution role."
  value       = module.iam_role.arn
}
