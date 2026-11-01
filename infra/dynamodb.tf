# All tables are on-demand (pay per request) - $0 when idle.

# Conversation transcript per session; items expire automatically via TTL.
resource "aws_dynamodb_table" "history" {
  name         = "${var.name}-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "ts"

  attribute {
    name = "session_id"
    type = "S"
  }
  attribute {
    name = "ts"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}

# Fake order database the get_order_status tool reads.
resource "aws_dynamodb_table" "orders" {
  name         = "${var.name}-orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }
}

# Seed orders from the same JSON the app uses locally. Day offsets are resolved
# against the apply time; ignore_changes below keeps later plans clean.

locals {
  seed_orders = jsondecode(file("${path.module}/../src/shophelper/data/orders.json"))
  seed_base   = timestamp()
}

resource "aws_dynamodb_table_item" "orders" {
  # Orders have different attribute sets, so key by index rather than by object.
  for_each   = { for i, o in local.seed_orders : o.order_id => i }
  table_name = aws_dynamodb_table.orders.name
  hash_key   = aws_dynamodb_table.orders.hash_key

  # Refund updates made by the app are expected drift.
  lifecycle {
    ignore_changes = [item]
  }

  item = jsonencode(merge(
    {
      order_id   = { S = local.seed_orders[each.value].order_id }
      customer   = { S = local.seed_orders[each.value].customer }
      item       = { S = local.seed_orders[each.value].item }
      total      = { N = tostring(local.seed_orders[each.value].total) }
      status     = { S = local.seed_orders[each.value].status }
      ordered_at = { S = formatdate("YYYY-MM-DD", timeadd(local.seed_base, "-${local.seed_orders[each.value].ordered_days_ago * 24}h")) }
    },
    can(local.seed_orders[each.value].delivered_days_ago) ? {
      delivered_at = { S = formatdate("YYYY-MM-DD", timeadd(local.seed_base, "-${local.seed_orders[each.value].delivered_days_ago * 24}h")) }
    } : {},
    can(local.seed_orders[each.value].eta_days) ? {
      estimated_delivery = { S = formatdate("YYYY-MM-DD", timeadd(local.seed_base, "${local.seed_orders[each.value].eta_days * 24}h")) }
    } : {},
    can(local.seed_orders[each.value].refund_amount) ? {
      refund_amount = { N = tostring(local.seed_orders[each.value].refund_amount) }
    } : {},
  ))
}
