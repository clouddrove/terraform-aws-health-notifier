output "lambda_name" {
  description = "Name of the handler Lambda function."
  value       = module.aws_health_notifier.lambda_name
}

output "table_name" {
  description = "Name of the DynamoDB state table."
  value       = module.aws_health_notifier.table_name
}
