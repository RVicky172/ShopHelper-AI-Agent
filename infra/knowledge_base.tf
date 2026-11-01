# Step 4: RAG over the store policies.
# S3 (documents) -> Bedrock Knowledge Base (Titan v2 embeddings) -> S3 Vectors (index).
# S3 Vectors bills per GB stored and per query - nothing while idle, unlike OpenSearch Serverless.

locals {
  account_id     = data.aws_caller_identity.current.account_id
  policy_dir     = "${path.module}/../knowledge/policies"
  policy_files   = fileset(local.policy_dir, "*.md")
  embedding_arn  = "arn:aws:bedrock:${var.region}::foundation-model/${var.embedding_model_id}"
  embedding_dims = 1024
}

resource "aws_s3_bucket" "kb_docs" {
  bucket        = "${var.name}-kb-docs-${local.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "kb_docs" {
  bucket                  = aws_s3_bucket.kb_docs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "policies" {
  for_each     = local.policy_files
  bucket       = aws_s3_bucket.kb_docs.id
  key          = "policies/${each.value}"
  source       = "${local.policy_dir}/${each.value}"
  etag         = filemd5("${local.policy_dir}/${each.value}")
  content_type = "text/markdown"
}

resource "aws_s3vectors_vector_bucket" "kb" {
  vector_bucket_name = "${var.name}-vectors-${local.account_id}"
  force_destroy      = true
}

resource "aws_s3vectors_index" "kb" {
  vector_bucket_name = aws_s3vectors_vector_bucket.kb.vector_bucket_name
  index_name         = "policies"
  data_type          = "float32"
  dimension          = local.embedding_dims
  distance_metric    = "cosine"

  # Bedrock stores the chunk text + its own metadata on each vector; these are
  # large, so they must be non-filterable or ingestion hits the filterable-size limit.
  metadata_configuration {
    non_filterable_metadata_keys = ["AMAZON_BEDROCK_TEXT", "AMAZON_BEDROCK_METADATA"]
  }
}

# --- Role the Knowledge Base service assumes during ingestion and retrieval ---
data "aws_iam_policy_document" "kb_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
  }
}

resource "aws_iam_role" "kb" {
  name               = "${var.name}-kb-role"
  assume_role_policy = data.aws_iam_policy_document.kb_assume.json
}

data "aws_iam_policy_document" "kb" {
  statement {
    sid       = "Embed"
    actions   = ["bedrock:InvokeModel"]
    resources = [local.embedding_arn]
  }
  statement {
    sid       = "ReadDocs"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.kb_docs.arn, "${aws_s3_bucket.kb_docs.arn}/*"]
  }
  statement {
    sid = "Vectors"
    actions = [
      "s3vectors:PutVectors", "s3vectors:GetVectors", "s3vectors:DeleteVectors",
      "s3vectors:QueryVectors", "s3vectors:GetIndex", "s3vectors:ListVectors",
    ]
    resources = [aws_s3vectors_index.kb.index_arn]
  }
}

resource "aws_iam_role_policy" "kb" {
  role   = aws_iam_role.kb.id
  policy = data.aws_iam_policy_document.kb.json
}

resource "aws_bedrockagent_knowledge_base" "policies" {
  name     = "${var.name}-policies"
  role_arn = aws_iam_role.kb.arn

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = local.embedding_arn
      embedding_model_configuration {
        bedrock_embedding_model_configuration {
          dimensions          = local.embedding_dims
          embedding_data_type = "FLOAT32"
        }
      }
    }
  }

  storage_configuration {
    type = "S3_VECTORS"
    s3_vectors_configuration {
      index_arn = aws_s3vectors_index.kb.index_arn
    }
  }

  depends_on = [aws_iam_role_policy.kb]
}

resource "aws_bedrockagent_data_source" "policies" {
  name              = "${var.name}-policies-s3"
  knowledge_base_id = aws_bedrockagent_knowledge_base.policies.id

  # Vectors live in S3 Vectors; on destroy just drop them with the bucket.
  data_deletion_policy = "RETAIN"

  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn         = aws_s3_bucket.kb_docs.arn
      inclusion_prefixes = ["policies/"]
    }
  }

  vector_ingestion_configuration {
    chunking_configuration {
      chunking_strategy = "FIXED_SIZE"
      fixed_size_chunking_configuration {
        max_tokens         = 300
        overlap_percentage = 20
      }
    }
  }
}

# Re-sync the knowledge base whenever a policy document changes.
# A single aws CLI command runs the same under cmd.exe (Windows) and /bin/sh.
resource "terraform_data" "kb_sync" {
  triggers_replace = [for f in aws_s3_object.policies : f.etag]

  provisioner "local-exec" {
    command = "aws bedrock-agent start-ingestion-job --region ${var.region} --knowledge-base-id ${aws_bedrockagent_knowledge_base.policies.id} --data-source-id ${aws_bedrockagent_data_source.policies.data_source_id}"
  }
}
