---
title: Choosing a database
checked: 2026-11-06
---

## What you'll learn

- The main kinds of database, and what each is for
- What an AI app really needs to store
- Why transactions matter
- How to choose, and what this project didn't build

## The simple explanation

Different databases are good at different questions:

| Kind | Picture | Good at | Examples |
| --- | --- | --- | --- |
| **Relational** | Linked spreadsheets with strict columns | Relationships, and changes that must be exact | Postgres, MySQL |
| **Key-value** | A coat check: one ticket, one coat | Fast lookups at huge scale | DynamoDB, Redis |
| **Document** | A folder per customer | Flexible records read as a whole | MongoDB |
| **Vector** | Finding things by meaning | Similarity search | pgvector, Qdrant |

An AI app isn't one kind of data. It has users and orders, conversation history, saved agent state, and embeddings. It's tempting to pick a specialist for each, but each one is another thing to run, secure and back up.

The good default: **start with one general database, and add another only when you can name what the first can't do.**

A **transaction** is the main reason to prefer a relational database for anything involving money. Think of a bank transfer. Taking $100 from one account and adding it to another must both happen, or neither. A transaction gives you that promise.

## An example

Two browser tabs press **Place order** at the same moment. The cart holds one item. How many orders should exist?

One. Here's how the database guarantees it:

```python file=src/shophelper/shop/cart.py
DELETE FROM cart_items WHERE user_id = %s RETURNING product_id, quantity
```

The checkout **claims** the cart by deleting it, inside one transaction. Of two requests, only one gets the rows. The other finds an empty cart.

The first instinct is usually "read the cart, make the order, then clear the cart". That has a gap: both requests can read before either clears. Application code can't close that gap, but the database can.

Refund approval uses the same idea. When 8 reviewers raced for one refund in testing, exactly one won:

```python file=src/shophelper/shop/refunds.py
"UPDATE refund_requests SET status = 'claimed', reviewer_id = %s, note = %s "
"WHERE id = %s AND status = 'pending' RETURNING id",
```

## How ShopHelper does it

Locally, one Postgres holds everything:

| Data | Stored as | Why |
| --- | --- | --- |
| Users, sessions, carts, refunds | Normal tables | Relationships and exact rules |
| Orders | A JSONB `data` column, plus an owner | Shaped like the AWS records |
| Product details | A JSONB `specs` column | Each category has different fields |
| Chat history | A table | Listed by conversation |
| Agent state | LangGraph's checkpoint tables | So a paused refund survives a restart |
| Embeddings | A `VECTOR(768)` column | Search lives beside the data |

That's a relational database also doing document and vector work. **JSONB** stores flexible data in a column, and you can still query inside it:

```sql file=src/shophelper/core/schema.sql
data     JSONB NOT NULL
```

One practical reason this was chosen: the MCP server is a separate process, so keeping orders in memory meant it couldn't see refunds. A shared database fixed that, and pgAdmin lets you read everything.

On AWS the same code uses different storage, chosen when the app starts:

| Data | Local | AWS |
| --- | --- | --- |
| Orders, history, agent state | Postgres | DynamoDB |
| Embeddings | pgvector | S3 Vectors |
| Accounts | Postgres | Not built |

Why DynamoDB there? It costs nothing when idle, and there's no server to run, which suits a learning project. That choice has a real limit: this project's orders have no owners there, because the owner lookup is only built for Postgres. It's written plainly in the code:

```python file=src/shophelper/shop/orders.py
return None  # DynamoDB orders have no owners: accounts are never enabled on this backend
```

**What this project doesn't do:**

- **Migrations.** `schema.sql` is run on every start, using `IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS`. That's fine here. A real product needs a versioned tool like [Alembic](https://alembic.sqlalchemy.org/), so each change is recorded and can be applied in order.
- **A pool for every query.** Most database calls open a short-lived connection, and only LangGraph's checkpointer uses a pool. Under real traffic, a pool would save connection time, and stop you hitting the server's limit.

## In the market

Checked on 2026-11-06.

| Database | Reach for it when |
| --- | --- |
| [Postgres](https://www.postgresql.org/docs/current/datatype-json.html) | The default for most products, with JSONB and pgvector included |
| [DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html) | You know your access patterns, and need serverless scale |
| [MongoDB](https://www.mongodb.com/docs/) | Your data really is nested documents of many shapes |
| [Redis](https://redis.io/docs/latest/) | Caching, rate limits and short-lived data |

**How to choose:**

1. Does it involve money or strict rules? Use a relational database.
2. Do you know every query in advance, and need huge scale with little operation? Consider key-value.
3. Is it short-lived, and safe to lose? Use a cache.
4. Is it only for search? See [vector databases](../05-rag/05-vector-databases.md).

Key-value stores need a different way of thinking. With DynamoDB you design the table around the questions you'll ask, and a new kind of question can mean a new index. With Postgres, you can usually just write a new query.

## Try it

1. Open pgAdmin at http://localhost:5050, and open the Query Tool on the ShopHelper database.
2. Query inside the JSON:

```sql
SELECT data->>'status' AS status, count(*)
FROM orders
GROUP BY 1
ORDER BY 2 DESC;
```

3. Join normal columns with JSON in one query:

```sql
SELECT u.display_name, o.order_id, o.data->>'item' AS item
FROM orders o
JOIN users u ON u.id = o.owner_id
LIMIT 5;
```

4. See how much the agent's memory takes, next to everything else:

```sql
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

## Interview questions

### What database would you choose for an AI support agent?

**Strong answer:** Postgres, unless something rules it out. Users, orders and refunds need relationships and transactions. JSONB covers flexible records, and pgvector covers search, so one system holds it all. Agent state can go there too, through a checkpointer. I'd add Redis for caching or rate limits if I needed to. In my project, one Postgres holds it all locally, and AWS uses DynamoDB because it costs nothing when idle.

**Follow-up:** What would make you move conversations out of Postgres?

### Two requests try to take the same thing at once. How do you handle it?

**Strong answer:** I let the database decide, with one atomic statement. For refunds I use `UPDATE ... WHERE status = 'pending' RETURNING id`, so only one reviewer gets a row back. For checkout, `DELETE ... RETURNING` claims the cart. A read followed by a write leaves a gap that application code can't close. I test it with real concurrency: 8 reviewers raced, and exactly one won.

**Follow-up:** When would you use a lock instead?

### How do you change a database schema safely in production?

**Strong answer:** With versioned migrations, applied in order, and tracked by a tool. I'd make changes in steps: add the new column, write to both, backfill, switch reads, then remove the old one, so old and new code can run together during a deployment. My learning project just runs an idempotent schema file on start, which wouldn't be enough for a real product.

**Follow-up:** How do you add an index to a large table?

## Check yourself

### Why does checkout delete the cart inside the transaction?

- [x] So only one of two requests can claim it — right: the other finds it empty.
- [ ] To save disk space — that's a side effect.
- [ ] Because carts expire — this isn't about time.

### What's the good default for a new product?

- [ ] One specialist database per kind of data — that's a lot to run.
- [x] One general database, until you can name its limit — right: add others for a reason.
- [ ] Whatever is newest — that isn't a reason.

### Why does JSONB suit product specs?

- [ ] It's always faster — not always.
- [ ] Postgres has no other option — it has normal columns.
- [x] Each category has different fields — right: and you can still query inside it.
