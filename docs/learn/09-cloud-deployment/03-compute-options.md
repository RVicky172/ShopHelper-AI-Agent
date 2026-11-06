---
title: Compute options
checked: 2026-11-06
---

## What you'll learn

- The main ways to run an agent on AWS
- What was measured for Lambda and Fargate
- Why agents are awkward for serverless
- How to choose

## The simple explanation

There are three broad ways to pay for computing:

| Style | Picture | You pay for | AWS example |
| --- | --- | --- | --- |
| **Serverless** | A taxi | Each trip | Lambda |
| **Containers** | A leased car | Time, used or not | ECS Fargate |
| **Managed agent runtime** | A chauffeur service | Sessions, with the driving handled | Bedrock AgentCore |

A taxi is cheap for an occasional trip, and it may take a moment to arrive. A leased car is ready at the door, and costs the same when parked.

Agents don't fit neatly. A normal web request takes milliseconds. An agent turn takes seconds, mostly **waiting** for a model, and it may stream. Some run for minutes. So the usual assumption of "short and stateless" breaks down.

## An example

This project ran the **same image** on both, in Mumbai, measured from India:

| Measurement | Lambda + API Gateway | ECS Fargate + load balancer |
| --- | --- | --- |
| First request, version 1 | **20.7 s** | Not applicable, already warm |
| First request, version 2 | **4.2 s** | Not applicable |
| Warm `/health` | 0.24 s | 0.24 s |
| A blocked `/chat`, no model call | About 0.5 s | About 0.5 s |

That 20.7 seconds is the interesting number. The app's imports took about 6.8 seconds on a cold Lambda, and starting the MCP server added 3 more. That passed Lambda's 10-second limit for starting up, so Lambda killed it and began again.

Two fixes brought it down to 4.2 seconds: Lambda calls tools in-process, and a setting finishes a long start during the first request:

```hcl file=infra/lambda.tf
AWS_LWA_ASYNC_INIT = "true"
```

Nobody would have predicted that from reading docs. It came from deploying and measuring. Full chat latency on AWS is still unmeasured, because no real Claude call ran.

## How ShopHelper does it

One Dockerfile serves both. On Lambda, a small adapter turns each invoke into an HTTP request to the same app:

```dockerfile file=Dockerfile
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
```

| | Lambda + API Gateway | ECS Fargate + load balancer |
| --- | --- | --- |
| Cold starts | Yes, about 4 s here | No, but a new task takes 1 to 2 minutes |
| Streaming | API Gateway buffers it | Native |
| Longest request | 30 s | 120 s idle timeout here |
| Concurrency | One request per environment | Many per task |
| Idle cost | $0 | About $1.56 a day |
| Work to run it | Little | Task size, network, scaling |

**Streaming** decides it for a chat UI. On Lambda with API Gateway, all the tokens arrive at once. So the chat runs on Fargate behind the load balancer, with its timeout raised.

**Concurrency** matters more than it looks. An agent turn spends most of its time waiting for a model. A Fargate task can wait on many at once, because FastAPI is async. Lambda runs one request per environment, so you pay for each wait separately.

**When does each win on price?** A 5-second turn on 2 GB of Lambda is 10 GB-seconds, about $0.00017. Add the request charges, and it's about $0.00017 a turn. Fargate's rent is about $47 a month. So they break even near **280,000 turns a month**, or about 9,000 a day. Under that, Lambda is cheaper. That ignores the free tier, and it assumes one task can keep up. In both cases the model costs far more than the compute, as [the cost lesson](08-cost.md) shows.

## In the market

Checked on 2026-11-06.

| Option | Good for | Watch for |
| --- | --- | --- |
| **Lambda** | Spiky traffic, short turns | Timeouts. [Response streaming](https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html) exists, up to 200 MB, but not through this API Gateway setup |
| **ECS Fargate** | Streaming, steady traffic | Rent, and more to configure |
| **EKS, Kubernetes** | Many services, an existing platform team | A lot of work for one app |
| **[AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)** | Long agent sessions, managed for you | Newer, and tied to AWS. Its [quota page](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/bedrock-agentcore-limits.html) lists long session limits, so check them for your case |
| **EC2** | Full control, GPUs | You patch and scale it |

**Long-running work.** If a job takes minutes, don't hold a web request open. Accept it, return an id, run it from a queue, and let the client check back or stream the result. [Scaling](07-scaling-and-rate-limits.md) goes into this.

**How to choose:**

1. Short turns, spiky traffic, no streaming? Lambda.
2. Streaming, long turns, steady traffic? Containers.
3. Long sessions, and you want less to build? Compare a managed runtime.
4. Already have a Kubernetes platform? Use it. Don't build one for this.

## Try it

1. Read `infra/lambda.tf` and `infra/ecs.tf`. Find the memory size, the timeout and the task size.
2. In `Dockerfile`, find the two lines that make one image work in both.
3. Work out the break-even for a 10-second turn, and for 1 GB of Lambda.
4. Why does Lambda use in-process tools, when Fargate uses MCP?

## Interview questions

### Lambda or containers for an AI agent?

**Strong answer:** It depends on streaming, turn length and traffic. Lambda is great for spiky, short work, and costs nothing idle. But turns mostly wait on a model, and you pay for that wait, one request per environment. Containers handle many waits at once, and stream properly. I ran the same image on both. API Gateway buffered the stream, so the chat belongs on containers, and Lambda is fine for non-streaming calls.

**Follow-up:** How would you stream on Lambda?

### What's a cold start, and how have you dealt with one?

**Strong answer:** It's the time to start a new environment before serving a request. Mine took 20.7 seconds at first: imports took 6.8 seconds, and starting the MCP subprocess added 3 more, which passed Lambda's 10-second limit, so it restarted. I moved tools in-process on Lambda, and used async init, which brought it to 4.2 seconds. I'd also trim imports, or use provisioned concurrency if the traffic justified it.

**Follow-up:** Why was it slower than on your laptop?

### How would you run an agent task that takes 20 minutes?

**Strong answer:** Not in a web request. I'd accept it, return an id, and put it on a queue, with a worker that saves progress so it can resume. The client polls or subscribes for updates. LangGraph's checkpoints help with resuming. I'd compare a managed runtime too, since it's built for long sessions. And I'd set a budget per task, so a loop can't run forever.

**Follow-up:** What happens if the worker dies halfway?

## Check yourself

### Why did API Gateway rule out Lambda for the chat?

- [x] It buffers the response, so streaming doesn't work — right: tokens arrive all at once.
- [ ] It can't run Python — Lambda runs the image.
- [ ] It's too expensive — it's cheap here.

### Why does an agent suit containers better than a normal API?

- [ ] It uses less memory — memory isn't the point.
- [x] Turns mostly wait, and a task can wait on many at once — right: async handles that.
- [ ] Containers have GPUs — these don't.

### What caused the 20.7-second first request?

- [ ] A slow model — no model ran.
- [ ] The network — that wasn't it.
- [x] Startup passed Lambda's 10-second limit, so it restarted — right: found by measuring.
