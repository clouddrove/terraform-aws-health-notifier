output "lambda_name" {
  description = "Name of the handler Lambda function."
  value       = module.aws_health_notifier.lambda_name
}

output "rule_arn" {
  description = "ARN of the EventBridge rule capturing AWS Health events."
  value       = module.aws_health_notifier.rule_arn
}

output "dlq_url" {
  description = "URL of the dead letter queue."
  value       = module.aws_health_notifier.dlq_url
}

output "table_name" {
  description = "Name of the DynamoDB state table."
  value       = module.aws_health_notifier.table_name
}
