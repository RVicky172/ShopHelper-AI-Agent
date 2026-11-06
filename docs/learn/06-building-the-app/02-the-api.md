---
title: The API
checked: 2026-11-06
---

## What you'll learn

- What the API layer should and shouldn't do
- How a request is checked before your code runs
- What the common status codes mean here
- When to use `def` or `async def` in FastAPI

## The simple explanation

The API is the waiter in a restaurant. It takes an order in a set format, checks it makes sense, passes it to the kitchen, and brings back the result. It doesn't cook.

So routes should stay thin. A route does four jobs:

1. Check the shape of the request.
2. Work out who's asking.
3. Call the code that does the real work.
4. Turn the result into a response.

Anything else, such as refund rules, belongs in the feature's folder.

**Validation at the door.** Everything from outside is untrusted. So describe what a valid request looks like, and let the framework refuse the rest before your code runs.

**Status codes** tell the caller what happened, in a way code can act on:

| Code | Meaning | Here |
| --- | --- | --- |
| 200, 201 | It worked | Chat answered, conversation created |
| 401 | Who are you? | Not signed in |
| 403 | You can't do that | A customer reviewing a refund |
| 404 | Not found | Another person's conversation |
| 409 | Conflict with current state | The refund was already taken |
| 422 | Your request is malformed | A required field is missing |

## An example

Here are real replies from this API while building these lessons.

No session cookie:

```text
401  {"detail":"Sign in first"}
```

Signed in, but `session_id` is missing:

```text
422  {"detail":[{"type":"missing","loc":["body","session_id"],"msg":"Field required", ...}]}
```

No handler code ran for that one. The model below refused it.

Signed in, but the conversation doesn't exist:

```text
404  {"detail":"No such conversation"}
```

Someone else's conversation gets the same 404. If it gave a 403, an attacker could learn which ids exist.

That makes three layers, each stopping a different problem, before the agent ever starts.

## How ShopHelper does it

The request is a Pydantic model. Limits are part of the type:

```python file=src/shophelper/api/schemas.py
class ChatRequest(BaseModel):
message: str = Field(min_length=1, max_length=2000)
```

The length limit is a cost control too, because every character goes to a model.

Here's a whole route. Find the four jobs:

```python file=src/shophelper/api/app.py
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
principal = await run_in_threadpool(_owned_by_caller, request, req.session_id)
turn = app.state.service.chat(req.session_id, req.message, principal)
return await _observed("chat", req.session_id, turn)
```

**Heavy things are built once.** The agent, its tools and the database pool are created when the app starts, not on each request:

```python file=src/shophelper/api/app.py
app.state.service = ShopHelperService(tools=tools, checkpointer=checkpointer)
```

**`def` or `async def`?** One Python process handles many requests by switching between them whenever one is waiting. Blocking code inside `async def` stops all of them, including everyone's streams.

| Your code | Use | Why |
| --- | --- | --- |
| Awaits something | `async def` | It yields while waiting |
| Blocks, such as password hashing | `def` | [FastAPI runs it in a worker thread](https://fastapi.tiangolo.com/async/) |
| Blocks, inside an `async def` | `run_in_threadpool` | Moves that one call to a thread |

This project's database calls block, so that's what `run_in_threadpool` is doing in the route above.

**Errors have two audiences.** The log gets the full detail, and the caller gets a plain message. Sending stack traces to a browser gives attackers a map:

```python file=src/shophelper/api/app.py
log_event("chat_error", endpoint=endpoint, session_id=session_id, error=repr(exc)[:500])
yield f"event: error\ndata: {json.dumps('Something went wrong')}\n\n"
```

**Routers** split routes into files: `auth_routes.py`, `shop_routes.py` and `local_routes.py`. Local-only routes return 404 on AWS, so a new setting never changes what's deployed.

## In the market

Checked on 2026-11-06.

| Framework | Language | Good for |
| --- | --- | --- |
| [FastAPI](https://fastapi.tiangolo.com/) | Python | APIs, with validation and docs from types. Used here |
| [Flask](https://flask.palletsprojects.com/) | Python | Small services with few built-in opinions |
| [Django](https://www.djangoproject.com/) | Python | Full sites, with an admin and database layer included |
| [Next.js](https://nextjs.org/) | TypeScript | One codebase for the web app and its server |

Python is a common choice for AI backends, because most agent and model libraries arrive there first. That's what decided it here.

**REST or something else?** REST over JSON suits most products. GraphQL helps when many clients want different shapes of data. gRPC suits fast calls between your own services. Streaming is separate, and it's the [next lesson](03-streaming.md).

Not built here: **rate limiting** and **API versioning**. A public API needs both. [Stage 9](../09-cloud-deployment/01-running-locally.md) covers deploying it.

## Try it

1. Sign in to the shop at http://localhost:5173, then open http://localhost:8000/docs in the same browser. The page is generated from the types.
2. Open a private window, and go to the same page. You get `Sign in first`, because every route is protected unless listed as public.
3. Back in the signed-in window, open `POST /chat`, choose **Try it out**, delete `session_id`, and execute. Read the 422.

## Interview questions

### What belongs in an API route, and what doesn't?

**Strong answer:** A route checks the request, finds out who's asking, calls the real code, and shapes the response. Rules don't belong there, because then they can't be reused or tested without HTTP. In my project the refund limit is a function in `shop/`, and the route turns its exception into a 403. So the agent and the staff page can't drift apart.

**Follow-up:** How do you test a route?

### What's the danger of `async def` in FastAPI?

**Strong answer:** Async code shares one event loop. If something blocks in it, such as password hashing or a synchronous database call, every other request waits, including live streams. So I use plain `def` for blocking routes, which FastAPI runs in a thread pool, or `run_in_threadpool` for one call inside an async route. Password hashing is deliberately slow, so my login routes are plain `def`.

**Follow-up:** How would you notice this in production?

### Should a request for someone else's data return 403 or 404?

**Strong answer:** Usually 404, when the existence of the thing is itself private. A 403 confirms it exists, which lets an attacker map valid ids. In my project someone else's conversation and a missing one both return the same 404. I'd use 403 when the caller already knows the thing exists, like a support agent trying to approve a refund above their limit.

**Follow-up:** What about timing differences?

## Check yourself

### A request is missing a required field. What should come back?

- [x] 422, before your code runs — right: the model refuses it at the door.
- [ ] 500 — that means the server failed.
- [ ] 200 with an error message — then code can't tell it failed.

### A route needs to hash a password. How should it be written?

- [ ] `async def`, calling the hash directly — that blocks everyone.
- [x] Plain `def`, so it runs in a worker thread — right: the event loop stays free.
- [ ] It doesn't matter — it matters a lot for live streams.

### Why not send the full error to the browser?

- [ ] Browsers can't display it — they can.
- [ ] It would be too slow — speed isn't the issue.
- [x] It tells attackers how the system works — right: logs get the detail.
