# Minimal VPC for ECS: two public subnets, no NAT gateway (~$1/day saved).
# Fargate tasks get public IPs to reach ECR/Bedrock; their security group only
# accepts traffic from the ALB.

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  count                = var.enable_ecs ? 1 : 0
  cidr_block           = "10.20.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = var.name }
}

resource "aws_internet_gateway" "main" {
  count  = var.enable_ecs ? 1 : 0
  vpc_id = aws_vpc.main[0].id
}

resource "aws_subnet" "public" {
  count                   = var.enable_ecs ? 2 : 0
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = cidrsubnet("10.20.0.0/16", 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.name}-public-${count.index}" }
}

resource "aws_route_table" "public" {
  count  = var.enable_ecs ? 1 : 0
  vpc_id = aws_vpc.main[0].id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }
}

resource "aws_route_table_association" "public" {
  count          = var.enable_ecs ? 2 : 0
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_security_group" "alb" {
  count  = var.enable_ecs ? 1 : 0
  name   = "${var.name}-alb"
  vpc_id = aws_vpc.main[0].id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "task" {
  count  = var.enable_ecs ? 1 : 0
  name   = "${var.name}-task"
  vpc_id = aws_vpc.main[0].id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb[0].id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
