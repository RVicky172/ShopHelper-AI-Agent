# Least-privilege permissions for the running app - shared by the Lambda execution
# role and the ECS task role so both deployments behave identically.

locals {
  langsmith_param = "/${var.name}/langsmith-api-key"
  model_ids       = [var.agent_model_id, var.judge_model_id]
  # "global." profiles route to any commercial region, so the underlying
  # foundation-model ARNs are region-less / any-region.
  base_model_ids = [for m in local.model_ids : replace(m, "/^(global|apac|in|us|eu)\\./", "")]
}

data "aws_iam_policy_document" "app" {
  statement {
    sid     = "InvokeClaude"
    actions = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = concat(
      [for m in local.model_ids : "arn:aws:bedrock:${var.region}:${local.account_id}:inference-profile/${m}"],
      [for m in local.base_model_ids : "arn:aws:bedrock:*::foundation-model/${m}"],
      [for m in local.base_model_ids : "arn:aws:bedrock:::foundation-model/${m}"],
    )
  }
  statement {
    sid       = "Guardrail"
    actions   = ["bedrock:ApplyGuardrail"]
    resources = [aws_bedrock_guardrail.main.guardrail_arn]
  }
  statement {
    sid       = "KnowledgeBase"
    actions   = ["bedrock:Retrieve"]
    resources = [aws_bedrockagent_knowledge_base.policies.arn]
  }
  statement {
    sid = "Tables"
    actions = [
      "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem",
      "dynamodb:Query", "dynamodb:BatchGetItem", "dynamodb:BatchWriteItem",
    ]
    resources = [
      aws_dynamodb_table.history.arn,
      aws_dynamodb_table.orders.arn,
      aws_dynamodb_table.checkpoints.arn,
    ]
  }
  statement {
    sid       = "LangSmithKey"
    actions   = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:${var.region}:${local.account_id}:parameter${local.langsmith_param}"]
  }
}

resource "aws_iam_policy" "app" {
  name   = "${var.name}-app"
  policy = data.aws_iam_policy_document.app.json
}

locals {
  # Same configuration for both runtimes; only RUNTIME differs.
  app_env = {
    AGENT_MODEL_ID          = var.agent_model_id
    JUDGE_MODEL_ID          = var.judge_model_id
    ORDERS_TABLE            = aws_dynamodb_table.orders.name
    HISTORY_TABLE           = aws_dynamodb_table.history.name
    CHECKPOINT_TABLE        = aws_dynamodb_table.checkpoints.name
    KNOWLEDGE_BASE_ID       = aws_bedrockagent_knowledge_base.policies.id
    GUARDRAIL_ID            = aws_bedrock_guardrail.main.guardrail_id
    GUARDRAIL_VERSION       = aws_bedrock_guardrail_version.main.version
    TOOLS_TRANSPORT         = var.tools_transport
    LANGSMITH_API_KEY_PARAM = local.langsmith_param
    LANGSMITH_PROJECT       = var.name
  }
}
