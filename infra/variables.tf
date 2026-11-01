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
  description = "Image tag for Lambda/ECS. Empty = the most recently pushed image in ECR (normal case; scripts/release.sh pushes and rolls out new tags)."
  type        = string
  default     = ""
}

variable "enable_ecs" {
  description = "Fargate + ALB + public IPv4 cost ~$1.5/day while running. Set false to keep only the Lambda deployment."
  type        = bool
  default     = true
}

variable "github_repo" {
  description = "owner/repo allowed to assume the CI deploy role via OIDC."
  type        = string
  default     = "RVicky172/ShopHelper-AI-Agent"
}

variable "tools_transport" {
  description = "ECS tool transport: local = in-process, mcp = via the FastMCP server (stdio). Lambda always uses local."
  type        = string
  default     = "mcp"
}
