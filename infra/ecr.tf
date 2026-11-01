resource "aws_ecr_repository" "app" {
  name                 = var.name
  image_tag_mutability = "IMMUTABLE" # every deploy is a new tag (git SHA)
  force_delete         = true        # lets `terraform destroy` remove it with images inside

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the last 10 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 10 }
      action       = { type = "expire" }
    }]
  })
}

# So a plain `terraform apply` never points Lambda/ECS at a stale or missing tag.
data "aws_ecr_image" "latest" {
  count           = var.image_tag == "" ? 1 : 0
  repository_name = aws_ecr_repository.app.name
  most_recent     = true
}

locals {
  image_uri = (var.image_tag != ""
    ? "${aws_ecr_repository.app.repository_url}:${var.image_tag}"
  : "${aws_ecr_repository.app.repository_url}@${data.aws_ecr_image.latest[0].image_digest}")
}
