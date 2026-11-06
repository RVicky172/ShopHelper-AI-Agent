---
title: Vector databases in the market
checked: 2026-11-06
---

## What you'll learn

- The three kinds of vector store
- How to estimate the size you'll need
- When Postgres is enough
- How to choose without trusting the marketing

## The simple explanation

Once you have vectors, they need a home. There are three broad kinds:

| Kind | Picture | Examples |
| --- | --- | --- |
| **An extension to your database** | Adding a shelf to the shop you already own | pgvector |
| **A dedicated vector database** | A purpose-built warehouse | Pinecone, Qdrant, Weaviate |
| **Vectors in cheap storage** | Off-site storage: cheap, but slower to fetch from | S3 Vectors |

A shelf in your own shop is the easy choice until it's full. You already know how to run it, and everything's in one place. A warehouse is built for volume, but it's one more building to run, and now your stock lives in two places.

That second point is the cost people forget. With a separate store, you need to keep it in step with your main data. If a document is deleted in one place and not the other, search returns something that no longer exists.

## An example

Work out the size before you choose anything. Our test of 50,000 vectors with 768 dimensions measured 201 MB of table and 196 MB of HNSW index. That's about 8 KB per vector.

| Vectors | Roughly | What that suggests |
| --- | --- | --- |
| 24 (ShopHelper today) | 456 KB, with all its text | Anything works |
| 100,000 | 800 MB | One small Postgres server |
| 10 million | 80 GB | Postgres can work, with a large server and care |
| 1 billion | 8 TB | A specialist store, or smaller vectors |

These are straight multiplication from one measurement, so treat them as a first guess. HNSW also works best when the index fits in memory, so memory is often the limit, more than disk.

Now ask the second question: **how many searches per second, and how fast must they be?** A support bot's knowledge base might see a few searches a second. A shopping site's recommendations might see thousands.

For most company knowledge bases, those two answers point to Postgres.

## How ShopHelper does it

ShopHelper uses both ends of that table:

| | Local | AWS |
| --- | --- | --- |
| **Store** | pgvector, in the same Postgres as orders | S3 Vectors, behind a Knowledge Base |
| **Why** | Nothing else to run, and you can read it in pgAdmin | Nothing to run, and it's cheap when idle |

Locally, vectors are just a column:

```sql file=src/shophelper/core/schema.sql
embedding    VECTOR(768) NOT NULL,     -- must equal the embedding model's dimensions
```

That comment matters. The column size is tied to the embedding model. **Changing the model means re-embedding every document**, whichever store you use, because vectors from different models can't be compared. That's the real lock-in here, more than the database.

The agent's tool hides the difference, so it searches the same way in both environments:

```python file=src/shophelper/agent/tools.py
def search_policy(query: str, top_k: int = 4) -> dict[str, Any]:
```

## In the market

Checked on 2026-11-06. These claims come from the vendors, and we haven't tested them.

| Store | Kind | What it says about itself |
| --- | --- | --- |
| [pgvector](https://github.com/pgvector/pgvector) | Postgres extension | Exact and approximate search, alongside your normal data |
| [S3 Vectors](https://aws.amazon.com/blogs/aws/amazon-s3-vectors-now-generally-available-with-increased-scale-and-performance/) | Object storage | Up to 2 billion vectors per index, and [under 1 second for infrequent queries, as low as 100 ms for frequent ones](https://aws.amazon.com/about-aws/whats-new/2026/03/s3-vectors-expands-17-regions/) |
| [OpenSearch](https://docs.aws.amazon.com/prescriptive-guidance/latest/choosing-an-aws-vector-database-for-rag-use-cases/vector-db-options.html) | Search engine | Keyword and vector together, and AWS's suggestion for high query rates at low delay |
| [Qdrant](https://qdrant.tech/documentation/search/hybrid-queries/) | Dedicated | Built-in hybrid queries |
| [Weaviate](https://docs.weaviate.io/weaviate/concepts/search/hybrid-search) | Dedicated | Built-in hybrid search |
| [Pinecone](https://docs.pinecone.io/guides/search/reciprocal-rank-fusion) | Dedicated, managed | A hosted service, so nothing to operate |

We've left prices out on purpose. The ones we found disagreed and came from blogs, and the cost depends on your size and traffic anyway. Be careful with speed claims too: published comparisons often come from a vendor, on data that isn't yours.

**How to choose:**

1. Already on Postgres, under a few million vectors? Start with pgvector.
2. Large, and searched rarely? Consider cheap storage like S3 Vectors.
3. High traffic, low delay, or heavy filtering? Compare dedicated options.
4. Then load a real sample into your top two, and measure recall, delay and cost.

## Try it

1. Open pgAdmin at http://localhost:5050, and open the Query Tool on the ShopHelper database.
2. See how much space all of ShopHelper's knowledge takes:

```sql
SELECT pg_size_pretty(pg_total_relation_size('policy_chunks')), count(*)
FROM policy_chunks;
```

3. Use the same database to mix vectors and normal columns. Find the chunks nearest to the first refund chunk, in other documents only:

```sql
SELECT b.source, b.chunk_index,
       round((1 - (a.embedding <=> b.embedding))::numeric, 3) AS similarity
FROM policy_chunks a
JOIN policy_chunks b ON a.source <> b.source
WHERE a.source = 'refunds.md' AND a.chunk_index = 0
ORDER BY a.embedding <=> b.embedding
LIMIT 5;
```

A join like that is what you give up with a separate store.

## Interview questions

### When would you use pgvector rather than a dedicated vector database?

**Strong answer:** I'd use pgvector when I already run Postgres and the data fits comfortably, which covers most company knowledge bases. There's one system to back up and secure, and vectors can be joined and filtered with normal data, without keeping two stores in step. I'd move when size, query rate or delay needs outgrow it, and I'd prove that with a test on real data. My project uses pgvector locally, and S3 Vectors on AWS.

**Follow-up:** What would you measure to decide you've outgrown it?

### How do you estimate the storage for a vector store?

**Strong answer:** Each dimension is 4 bytes, so 768 dimensions is about 3 KB of raw vector. Then add the text and the index. I measured 50,000 vectors at about 8 KB each, including an HNSW index. So 10 million is roughly 80 GB. I'd check that against memory too, since HNSW works best when the index fits in it. Fewer dimensions or smaller numbers can cut that, at some cost in quality.

**Follow-up:** What else grows with the vector count?

### What's the hardest part of moving to a new embedding model?

**Strong answer:** Vectors from different models can't be compared, so every document has to be re-embedded, and the column size may change too. I'd build the new set beside the old one, test retrieval on both with the same questions, then switch over, and keep the old set until I'm sure. Queries must use the same model as the stored vectors, so the switch has to be clean.

**Follow-up:** How would you do that without any downtime?

## Check yourself

### What's a hidden cost of a separate vector database?

- [x] Keeping it in step with your main data — right: deletes and changes must reach both.
- [ ] It can't store text — most can.
- [ ] It can't be used with RAG — that's what it's for.

### You change embedding model. What must happen?

- [ ] Nothing: vectors are interchangeable — they can't be compared.
- [ ] You must change database — the store isn't the issue.
- [x] Every document is re-embedded — right: this applies in any store.

### Your company has 200,000 documents in Postgres already. Where do you start?

- [ ] A billion-scale dedicated store — that's more than you need.
- [x] pgvector, then measure — right: it's the least to run.
- [ ] A vendor benchmark — it's not your data.
