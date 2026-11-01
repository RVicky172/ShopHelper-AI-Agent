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
