# Next steps (pick up from here)

## Status on 2026-11-04: local stack done

The whole project now runs locally with `docker compose up`: LM Studio for the models, Postgres and
pgvector for all data, a React UI, and pgAdmin. See [local-setup.md](local-setup.md). Nothing below
is needed for local work.

Before the next AWS deployment, know that these changed since the last one:

- The agent's system prompt gained rules while tuning for Qwen. Claude hasn't been evaluated with
  them, so step 7 below is the first real test.
- `/chat/stream` sends step events before the first token. Existing clients that read only `token`
  and `final` still work.
- The image has extra Python packages, so it's larger. Re-measure cold starts in step 8.
- `.env` still names the destroyed AWS resources. `scripts/deploy.sh` rewrites it. Until then, don't
  use it for host-side runs. `docker compose` ignores those values.

Not done: the React UI has no AWS hosting and talks to a local API only. Accounts are local too, so the deployed
API has no login. Don't host it publicly until a later feature adds Cognito.

## AWS status on 2026-11-01

Status on **2026-11-01**: all 12 steps of the build are written, tested offline (19 unit tests)
and were deployed and checked in AWS. Then **everything was destroyed** with `scripts/teardown.sh`
to stop charges. Nothing project-related is running in the AWS account.

What never ran: any real Claude call. Bedrock answered every one with
`Model use case details have not been submitted`. So the eval suite, real chat latency and
streaming time-to-first-token are still unmeasured.

## Your steps (manual, outside the code)

- [ ] **1. Submit the Anthropic use-case form.** AWS console → Bedrock (`ap-south-1`) → Model catalog
      → open any Claude model → fill in the use-case details. It takes ~15 minutes to activate. Check
      it worked with:
      ```bash
      aws bedrock-runtime converse --region ap-south-1 \
        --model-id global.anthropic.claude-haiku-4-5-20251001-v1:0 \
        --messages '[{"role":"user","content":[{"text":"hi"}]}]'
      ```
- [ ] **2. (Optional) LangSmith key.** smith.langchain.com → Settings → API keys. Paste it after
      `LANGSMITH_API_KEY=` in `.env` (git-ignored, never commit it). For CI tracing, also add it as
      the GitHub repository secret `LANGSMITH_API_KEY`.
- [ ] **3. After redeploying (step 4 below), confirm two emails** sent to the address in
      `infra/terraform.tfvars`: "AWS Notification - Subscription Confirmation" (alarms) and the
      budget notification. The old subscriptions were deleted by the teardown, so these are new ones.

## Steps to run (I can do these once 1 is done)

All from the repo root in Git Bash.

- [ ] **4. Recreate the infrastructure:** `scripts/deploy.sh` (~10 min). This also rewrites `.env`
      with the new Knowledge Base and Guardrail ids. They change on every deploy.
- [ ] **5. Smoke-test the agent locally:**
      `uv run python -m shophelper.agent.raw_agent "Where is order 1002?"`
- [ ] **6. LangSmith key to AWS** (if step 2 was done): `scripts/set_langsmith_key.sh`, then
      `scripts/release.sh`.
- [ ] **7. Run the evals:** `RUN_EVALS=1 uv run pytest evals -v`. The target is all 20 passing with
      faithfulness ≥ 4. Results land in `evals/report.json`.
- [ ] **8. Measure the two deployments:** `scripts/compare_deployments.sh`. Fill in the full `/chat`
      latency and streaming time-to-first-token in
      [deployment-comparison.md](deployment-comparison.md) and in the README comparison table.
- [ ] **9. Turn on CI deploys:** `scripts/set_github_vars.sh` (sets `AWS_DEPLOY_ENABLED=true` and the
      new resource ids). Push to `main` and check that the evals and deploy jobs go green.
- [ ] **10. Tear down again when finished:** `scripts/teardown.sh`. ECS + ALB cost ~$1.5/day while up.
      Lambda, DynamoDB and the KB cost ~$0 when idle.

## Cheaper option while testing

Set `enable_ecs = false` in `infra/terraform.tfvars` before step 4. This skips the VPC, ALB and
Fargate (the only part with an hourly cost) and keeps the Lambda deployment. Switch it back to
`true` only for step 8.

## Teardown check

`scripts/teardown.sh` ends by listing every resource still tagged `Project=ShopHelper`. An empty
list means nothing is left. The 2026-11-01 teardown result is recorded below.

**2026-11-01:** `terraform destroy` removed 89 resources. Six ECS task definition revisions that
`release.sh` had registered (outside Terraform) were deleted by hand, and the script now does this
itself. A service-by-service check found nothing left: Lambda, API Gateway, ALB, ECS, VPC/ENIs,
DynamoDB, S3, S3 Vectors, Knowledge Base, Guardrail, ECR repo, CloudWatch logs/dashboard/alarms,
SNS, SSM, IAM roles/policies, OIDC provider and the project budget. In the account but **not**
from this project, so left alone: ECR repo `sst-asset` and the budget "My Monthly Cost Budget".
CI deploys are switched off (`AWS_DEPLOY_ENABLED=false`).
