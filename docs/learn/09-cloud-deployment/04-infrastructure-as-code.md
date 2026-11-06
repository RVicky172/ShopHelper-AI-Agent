---
title: Infrastructure as code
checked: 2026-11-06
---

## What you'll learn

- What infrastructure as code gives you
- How Terraform's plan, apply and destroy work
- What state is, and why it's sensitive
- How this project keeps Terraform and CI apart

## The simple explanation

You can build cloud resources by clicking in a console. Then one day you need to know what you clicked.

**Infrastructure as code** describes what should exist in text files. A tool then makes it real.

Think of a recipe compared with cooking from memory. With a recipe you can make it again, a friend can review it, and you can see what changed. It's the same with a Terraform file.

It gives you four things:

| Benefit | Means |
| --- | --- |
| **Repeatable** | Build it again, exactly |
| **Reviewable** | Changes go through a pull request |
| **Removable** | One command takes it all down |
| **Documented** | The code says what exists |

Terraform has three main steps:

| Step | Does | Costs money? |
| --- | --- | --- |
| `terraform plan` | Shows what would change | No |
| `terraform apply` | Makes the changes | **Yes** |
| `terraform destroy` | Removes everything | Stops charges |

Always read the plan. It's your chance to notice "destroy database" before it happens.

## An example

Here's the budget alarm, the first thing created, before anything that costs money:

```hcl file=infra/budget.tf
resource "aws_budgets_budget" "monthly" {
limit_amount = tostring(var.monthly_budget_usd)
```

Removability really paid off here. When testing was finished, one teardown removed **89 resources**. Imagine finding and deleting 89 things by hand, across a dozen services. Something would've been missed, and it would've kept charging.

It wasn't perfect, and the gap is worth knowing. Six ECS task definitions had been made by the release script, outside Terraform, so Terraform didn't know about them. **Terraform only manages what it created.** The script now clears them too, and it ends by listing anything still tagged for this project.

## How ShopHelper does it

[infra/](../../../infra) has about 1,200 lines of Terraform, split by purpose: `lambda.tf`, `ecs.tf`, `dynamodb.tf`, `guardrail.tf` and so on.

**Every resource gets tags**, set once for all of them:

```hcl file=infra/versions.tf
Project   = "ShopHelper"
```

So one query can find everything this project made, which is how the teardown check works.

**State.** Terraform keeps a file recording what it created. Here it's local, and ignored by git:

```hcl file=infra/versions.tf
# State is kept locally (infra/terraform.tfstate, git-ignored). For a team you
```

State often contains sensitive values, so it should never be committed. A team would use a shared backend, such as S3, with locking, so two people can't change things at once.

**Code and infrastructure change at different speeds.** A new image ships many times a day, while a load balancer rarely changes. So CI deploys code, and Terraform is told to leave that one field alone:

```hcl file=infra/lambda.tf
ignore_changes = [image_uri]
```

CI's role stays small because of this. It can roll out an image, and it can't change the network. Infrastructure changes stay a deliberate step on a person's machine:

```hcl file=infra/github_oidc.tf
# CI deploys code (new image -> Lambda/ECS) and runs evals; infrastructure changes
```

**Keeping secrets out.** The LangSmith key is stored by a script, deliberately not by Terraform, so it never lands in state.

**Chicken and egg.** Lambda needs an image, and the image needs a repository. So the first deploy creates only the repository, pushes the image, then creates the rest:

```bash file=scripts/deploy.sh
terraform -chdir=infra apply -input=false -auto-approve -target=aws_ecr_repository.app
```

Note `-auto-approve`. It skips the plan review, and it's in a script you run on purpose. **Never run that script casually: it creates paid resources.**

**CI checks Terraform** without touching AWS, with `fmt` and `validate`. They catch syntax errors, and they can't catch a wrong permission.

## In the market

Checked on 2026-11-06.

| Tool | Language | Notes |
| --- | --- | --- |
| [Terraform](https://developer.hashicorp.com/terraform/language) | HCL | Works across clouds. Used here |
| OpenTofu | HCL | An open-source fork of Terraform |
| AWS CDK | TypeScript, Python | AWS only, and written in a normal language |
| AWS SAM | YAML | Focused on serverless |
| Pulumi | TypeScript, Python | Across clouds, in a normal language |

This project chose Terraform over SAM or CDK, because it's widely used, and it covers everything here in one tool.

**Drift** is when someone changes something by hand, and reality stops matching the code. `terraform plan` shows it. The usual rule is to make all changes through code.

**Modules** let you reuse groups of resources. This project doesn't use them, because there's only one environment. For dev, staging and production, you'd want them, or separate state per environment.

## Try it

These are safe. They don't touch AWS.

1. Run `terraform -chdir=infra fmt -check -recursive`.
2. Read `infra/lambda.tf`, and find what would change if you doubled the memory.
3. Find every `ignore_changes` in `infra/`, and say why each is there.
4. Read `.gitignore`, and find the lines that protect state.

## Interview questions

### Why use infrastructure as code?

**Strong answer:** It's repeatable, reviewable and removable. A change goes through a pull request, and a plan shows what will happen. For me the biggest win was removal: one command took down 89 resources, and tags let me check nothing was left. Six items had been made outside Terraform, which taught me it only manages what it created. So I'd keep everything in code.

**Follow-up:** How do you handle secrets in Terraform?

### How do you split infrastructure changes from code deployments?

**Strong answer:** They change at different speeds and risks. In my project CI ships new images, and Terraform ignores that one field, so it doesn't fight CI. Infrastructure changes stay a reviewed, deliberate step. That also keeps the CI role small: it can roll out an image, and it can't change networks.

**Follow-up:** Would a bigger team run Terraform in CI?

### What is Terraform state, and what can go wrong?

**Strong answer:** It's Terraform's record of what it created. If two people apply at once, it can be corrupted, so teams use a shared backend with locking. It can hold secrets, so it should be encrypted, and never committed. Mine is local, and ignored by git, which is fine for one person. If it's lost, Terraform no longer knows what it owns, and you have to import things back.

**Follow-up:** How would you recover a lost state file?

## Check yourself

### Which command shows changes without making them?

- [ ] `terraform apply` — that makes them.
- [x] `terraform plan` — right: read it every time.
- [ ] `terraform destroy` — that removes everything.

### Why did six task definitions need clearing by hand?

- [x] They were made outside Terraform — right: it only manages what it created.
- [ ] Terraform had a bug — it did what it should.
- [ ] They were in another region — they weren't.

### Why isn't state committed to git?

- [ ] It's too big — size isn't the reason.
- [ ] Git can't store it — it could.
- [x] It can hold sensitive values — right: treat it like a secret.
