# Step 10: metrics from structured logs, a dashboard and alarms.
# The app prints one JSON line per turn ({"event": "chat_completed", "input_tokens": ...});
# metric filters turn those into CloudWatch metrics for both Lambda and ECS.

locals {
  namespace = "ShopHelper"
  log_groups = {
    lambda = aws_cloudwatch_log_group.lambda.name
    ecs    = aws_cloudwatch_log_group.ecs.name
  }
  # metric name => (filter pattern, value)
  metrics = {
    Requests        = { pattern = "{ $.event = \"chat_completed\" }", value = "1" }
    InputTokens     = { pattern = "{ $.event = \"chat_completed\" }", value = "$.input_tokens" }
    OutputTokens    = { pattern = "{ $.event = \"chat_completed\" }", value = "$.output_tokens" }
    LatencyMs       = { pattern = "{ $.event = \"chat_completed\" }", value = "$.latency_ms" }
    GuardrailBlocks = { pattern = "{ $.event = \"chat_completed\" && $.status = \"blocked\" }", value = "1" }
    RefundsPending  = { pattern = "{ $.event = \"chat_completed\" && $.status = \"pending_approval\" }", value = "1" }
    Errors          = { pattern = "{ $.event = \"chat_error\" }", value = "1" }
  }
  metric_filters = merge([
    for lg_key, lg in local.log_groups : {
      for m, cfg in local.metrics : "${lg_key}-${m}" => merge(cfg, { log_group = lg, metric = m })
    }
  ]...)
}

resource "aws_cloudwatch_log_metric_filter" "app" {
  for_each       = local.metric_filters
  name           = "${var.name}-${each.key}"
  log_group_name = each.value.log_group
  pattern        = each.value.pattern

  metric_transformation {
    name       = each.value.metric
    namespace  = local.namespace
    value      = each.value.value
    unit       = each.value.metric == "LatencyMs" ? "Milliseconds" : "Count"
    dimensions = { Runtime = "$.runtime" }
  }
}

# --- Alarms -> email ---------------------------------------------------------
resource "aws_sns_topic" "alarms" {
  name = "${var.name}-alarms"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alert_email # AWS emails a confirmation link - click it
}

resource "aws_cloudwatch_metric_alarm" "app_errors" {
  for_each            = toset(["lambda", "ecs"])
  alarm_name          = "${var.name}-${each.key}-app-errors"
  alarm_description   = "Unhandled errors in ShopHelper chat turns (${each.key})."
  namespace           = local.namespace
  metric_name         = "Errors"
  dimensions          = { Runtime = each.key }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.name}-lambda-function-errors"
  alarm_description   = "Lambda invocation errors/timeouts."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.app.function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  count               = var.enable_ecs ? 1 : 0
  alarm_name          = "${var.name}-alb-target-5xx"
  alarm_description   = "ECS tasks returning 5xx through the ALB."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  dimensions          = { LoadBalancer = aws_lb.app[0].arn_suffix }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 3
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]
}

# --- Dashboard ---------------------------------------------------------------
locals {
  runtimes = ["lambda", "ecs"]
  # Claude Haiku 4.5 list price (USD per token) - check current Bedrock pricing.
  price_in  = 0.000001
  price_out = 0.000005

  per_runtime = { for m in ["InputTokens", "OutputTokens", "Requests", "Errors", "GuardrailBlocks"] :
    m => [for r in local.runtimes : [local.namespace, m, "Runtime", r]]
  }

  widgets = [
    { title = "Tokens (sum / 5 min)", stat = "Sum", metrics = concat(local.per_runtime.InputTokens, local.per_runtime.OutputTokens) },
    { title = "Requests", stat = "Sum", metrics = local.per_runtime.Requests },
    { title = "Latency p50 / p90 (ms)", stat = "p50", metrics = concat(
      [for r in local.runtimes : [local.namespace, "LatencyMs", "Runtime", r, { stat = "p50", label = "${r} p50" }]],
      [for r in local.runtimes : [local.namespace, "LatencyMs", "Runtime", r, { stat = "p90", label = "${r} p90" }]],
    ) },
    { title = "Errors & guardrail blocks", stat = "Sum", metrics = concat(local.per_runtime.Errors, local.per_runtime.GuardrailBlocks) },
    { title = "Estimated LLM cost (USD / 5 min)", stat = "Sum", metrics = [
      [local.namespace, "InputTokens", "Runtime", "lambda", { id = "il", visible = false }],
      [local.namespace, "InputTokens", "Runtime", "ecs", { id = "ie", visible = false }],
      [local.namespace, "OutputTokens", "Runtime", "lambda", { id = "ol", visible = false }],
      [local.namespace, "OutputTokens", "Runtime", "ecs", { id = "oe", visible = false }],
      [{ expression = "(FILL(il,0)+FILL(ie,0))*${local.price_in} + (FILL(ol,0)+FILL(oe,0))*${local.price_out}", label = "Agent model cost", id = "cost" }],
    ] },
    { title = "Lambda duration & invocations", stat = "Average", metrics = [
      ["AWS/Lambda", "Duration", "FunctionName", var.name, { stat = "p90", label = "Duration p90" }],
      ["AWS/Lambda", "Invocations", "FunctionName", var.name, { stat = "Sum", yAxis = "right" }],
    ] },
  ]
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = var.name
  dashboard_body = jsonencode({
    widgets = concat(
      [for i, w in local.widgets : {
        type   = "metric"
        x      = (i % 2) * 12
        y      = floor(i / 2) * 6
        width  = 12
        height = 6
        properties = {
          title   = w.title
          region  = var.region
          stat    = w.stat
          period  = 300
          view    = "timeSeries"
          metrics = w.metrics
        }
      }],
      [{
        type   = "log"
        x      = 0
        y      = 18
        width  = 24
        height = 6
        properties = {
          title  = "Lambda cold starts (Init Duration)"
          region = var.region
          view   = "table"
          query  = "SOURCE '${aws_cloudwatch_log_group.lambda.name}' | filter @type = \"REPORT\" | stats count(@initDuration) as coldStarts, avg(@initDuration) as avgInitMs, max(@initDuration) as maxInitMs, count(*) as invocations by bin(1h)"
        }
      }]
    )
  })
}
