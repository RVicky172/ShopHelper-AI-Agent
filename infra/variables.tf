variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "name" {
  description = "Prefix for every resource name."
  type        = string
  default     = "shophelper"
}

variable "alert_email" {
  description = "Receives budget and CloudWatch alarm emails (SNS needs you to click 'Confirm subscription')."
  type        = string
}

variable "monthly_budget_usd" {
  type    = number
  default = 10
}

variable "agent_model_id" {
  type    = string
  default = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "judge_model_id" {
  type    = string
  default = "global.anthropic.claude-sonnet-4-6"
}

variable "embedding_model_id" {
  type    = string
  default = "amazon.titan-embed-text-v2:0"
}

variable "image_tag" {
  description = "Container image tag deployed to Lambda and ECS. CI updates it after the first apply."
  type        = string
  default     = "bootstrap"
}

variable "enable_ecs" {
  description = "Fargate + ALB cost ~$0.75/day while running. Set false to keep only the Lambda deployment."
  type        = bool
  default     = true
}

variable "github_repo" {
  description = "owner/repo allowed to assume the CI deploy role via OIDC."
  type        = string
  default     = "RVicky172/ShopHelper-AI-Agent"
}

variable "tools_transport" {
  description = "local = tools in-process, mcp = tools via the FastMCP server (stdio)."
  type        = string
  default     = "mcp"
}
