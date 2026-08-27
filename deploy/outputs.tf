output "lambda_name" {
  description = "Name of the handler Lambda function."
  value       = module.aws_health_notifier.lambda_name
}

output "rule_name" {
  description = "Name of the EventBridge rule."
  value       = module.aws_health_notifier.rule_name
}

output "dlq_url" {
  description = "URL of the dead letter queue."
  value       = module.aws_health_notifier.dlq_url
}

output "table_name" {
  description = "Name of the DynamoDB state table."
  value       = module.aws_health_notifier.table_name
}
