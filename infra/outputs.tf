output "orders_table" {
  value = aws_dynamodb_table.orders.name
}

output "history_table" {
  value = aws_dynamodb_table.history.name
}

output "knowledge_base_id" {
  value = aws_bedrockagent_knowledge_base.policies.id
}

output "kb_data_source_id" {
  value = aws_bedrockagent_data_source.policies.data_source_id
}

output "guardrail_id" {
  value = aws_bedrock_guardrail.main.guardrail_id
}

output "guardrail_version" {
  value = aws_bedrock_guardrail_version.main.version
}

output "checkpoint_table" {
  value = aws_dynamodb_table.checkpoints.name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "lambda_function_name" {
  value = aws_lambda_function.app.function_name
}

output "api_gateway_url" {
  description = "Deployment 1: API Gateway -> Lambda"
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "alb_url" {
  description = "Deployment 2: ALB -> ECS Fargate"
  value       = var.enable_ecs ? "http://${aws_lb.app[0].dns_name}" : null
}

output "ecs_cluster" {
  value = var.enable_ecs ? aws_ecs_cluster.main[0].name : null
}

output "ecs_service" {
  value = var.enable_ecs ? aws_ecs_service.app[0].name : null
}
