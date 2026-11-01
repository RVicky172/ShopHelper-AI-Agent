output "orders_table" {
  value = aws_dynamodb_table.orders.name
}

output "history_table" {
  value = aws_dynamodb_table.history.name
}
