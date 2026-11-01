# Step 5: Bedrock Guardrail, applied by the app on the user input *before* the agent
# loop and on the final answer *after* it (ApplyGuardrail API). Billed per text unit
# assessed - nothing while idle.

resource "aws_bedrock_guardrail" "main" {
  name                      = "${var.name}-guardrail"
  description               = "Blocks prompt attacks and sensitive PII for the ShopHelper agent."
  blocked_input_messaging   = "Sorry, I can't help with that request. Please don't share card numbers, passwords or other sensitive details, and keep questions to orders and store policy."
  blocked_outputs_messaging = "Sorry, I can't share that. Please contact a human support agent."

  content_policy_config {
    # Jailbreaks / prompt injection. Only meaningful on input, so output strength must be NONE.
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
    dynamic "filters_config" {
      for_each = ["HATE", "INSULTS", "SEXUAL", "VIOLENCE", "MISCONDUCT"]
      content {
        type            = filters_config.value
        input_strength  = "MEDIUM"
        output_strength = "MEDIUM"
      }
    }
  }

  sensitive_information_policy_config {
    # Payment and credential data is never needed for support - block the whole message.
    dynamic "pii_entities_config" {
      for_each = [
        "CREDIT_DEBIT_CARD_NUMBER", "CREDIT_DEBIT_CARD_CVV", "PASSWORD",
        "US_SOCIAL_SECURITY_NUMBER", "AWS_ACCESS_KEY", "AWS_SECRET_KEY",
      ]
      content {
        type           = pii_entities_config.value
        action         = "BLOCK"
        input_action   = "BLOCK"
        output_action  = "BLOCK"
        input_enabled  = true
        output_enabled = true
      }
    }
    # Contact details are fine to receive but are masked before reaching the model/logs.
    dynamic "pii_entities_config" {
      for_each = ["EMAIL", "PHONE"]
      content {
        type           = pii_entities_config.value
        action         = "ANONYMIZE"
        input_action   = "ANONYMIZE"
        output_action  = "ANONYMIZE"
        input_enabled  = true
        output_enabled = true
      }
    }
    # No built-in entity for India's Aadhaar number (12 digits, often grouped 4-4-4).
    regexes_config {
      name        = "AADHAAR"
      description = "Indian Aadhaar number"
      pattern     = "\\b[2-9][0-9]{3}[ -]?[0-9]{4}[ -]?[0-9]{4}\\b"
      action      = "BLOCK"
    }
  }
}

# Immutable snapshot the app pins to. Re-created whenever the guardrail changes.
resource "aws_bedrock_guardrail_version" "main" {
  guardrail_arn = aws_bedrock_guardrail.main.guardrail_arn
  description   = "Managed by Terraform"

  lifecycle {
    replace_triggered_by = [aws_bedrock_guardrail.main]
  }
}
