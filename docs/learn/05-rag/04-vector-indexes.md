---
title: Vector indexes
checked: 2026-11-06
---

## What you'll learn

- Why search slows down as data grows
- What exact and approximate search mean
- How HNSW and IVFFlat work
- What recall is, with measured numbers

## The simple explanation

To find the nearest vectors, the simple way is to compare the question with every stored vector. That's **exact search**. It can't miss anything, but the work grows with every row.

An **index** avoids most of that work. Vector indexes are **approximate**: they check only a small part of the data, so they're fast, but they can miss a true match. **ANN, approximate nearest neighbour**, is the name for this family.

Two common kinds:

**HNSW** builds a [graph in layers](https://arxiv.org/abs/1603.09320). Think of driving across a country. You start on motorways, which cover long distances in a few jumps. Then main roads, then streets near the address. The search starts in a sparse top layer, and drops down as it gets closer.

**IVFFlat** splits the vectors into groups. Think of a library. Instead of checking every book, you go to the two or three nearest shelves, and check only those.

The measure of what you gave up is **recall**. If the true 10 nearest chunks are known, and the index finds 8 of them, recall@10 is 0.8.

## An example

We tested this on a throwaway database: 50,000 random vectors with 768 dimensions, the same size as this project's. Each result is the median of a set of searches:

| Search | Time per query | Recall@10 |
| --- | --- | --- |
| Exact | 85 ms | 1.00 |
| HNSW, `ef_search` 40 (the default) | 2.2 ms | 0.28 |
| HNSW, `ef_search` 100 | 3.5 ms | 0.48 |
| HNSW, `ef_search` 200 | 4.5 ms | 0.60 |

`ef_search` is how many candidates the search keeps while walking the graph. Higher means slower and more accurate.

The speed is the headline: about 39 times faster than exact search. But look at that recall. Does HNSW really miss 7 in 10?

**Not on real text, as far as we can tell, but this test can't prove that.** Random numbers have no structure. Every vector is about as far from the question as every other, so "nearest" barely means anything. That's the hardest case an index can get. Real embeddings form clusters of related meaning, which is what these graphs rely on.

So take two lessons from this. The trade-off between speed and recall is real, and you can turn the dial. And recall has to be measured on your own data, by comparing the index with exact search.

Building the index took 23 seconds, and it was 196 MB beside a 201 MB table. So an index can double your storage.

## How ShopHelper does it

The index is one statement, and it names the distance measure:

```sql file=src/shophelper/core/schema.sql
CREATE INDEX IF NOT EXISTS policy_chunks_embedding_idx
ON policy_chunks USING hnsw (embedding vector_cosine_ops);
```

Here's an honest detail: **at 24 rows, this index isn't used.** Ask Postgres for its plan, and you see this:

```text
Sort
  Sort Key: (embedding <=> ...)
  ->  Seq Scan on policy_chunks
```

`Seq Scan` means it reads every row. The planner is right, because reading 24 rows is cheaper than walking a graph. So search here is exact, with perfect recall, and the index only starts to matter when the data grows.

The index was added because it's cheap at this size, and shows how the real thing is set up.

## In the market

Checked on 2026-11-06.

From the [pgvector docs](https://github.com/pgvector/pgvector):

| | No index | HNSW | IVFFlat |
| --- | --- | --- | --- |
| **Recall** | Perfect | Approximate | Approximate |
| **Query speed** | Slowest | Better trade-off than IVFFlat | Lower |
| **Build time** | None | Slower | Faster |
| **Memory** | Least | More | Less |
| **Needs data first** | No | No, it can start empty | Yes, to form its groups |

Most teams start with HNSW. Its main settings are `m` and `ef_construction` at build time, and `ef_search` at query time.

Two limits are worth knowing:

- **Dimensions.** pgvector can index up to 2,000 dimensions for `vector`, and 4,000 for `halfvec`, which uses half-size numbers. Models with more need a workaround.
- **Filters.** With an approximate index, a `WHERE` filter is applied after the index scan. So asking for the top 4 of one customer's documents can return fewer than 4. pgvector offers iterative scans to deal with this.

## Try it

1. Open pgAdmin at http://localhost:5050, and open the Query Tool on the ShopHelper database.
2. Run this, and look for `Seq Scan`:

```sql
EXPLAIN SELECT source FROM policy_chunks
ORDER BY embedding <=> (SELECT embedding FROM policy_chunks LIMIT 1)
LIMIT 4;
```

3. Now force the index, to prove it exists. Run these together, and look for `Index Scan using policy_chunks_embedding_idx`:

```sql
SET enable_seqscan = off;
EXPLAIN SELECT source FROM policy_chunks
ORDER BY embedding <=> (SELECT embedding FROM policy_chunks LIMIT 1)
LIMIT 4;
```

4. Put it back with `SET enable_seqscan = on;`.

## Interview questions

### What's the difference between exact and approximate vector search?

**Strong answer:** Exact search compares the query with every vector, so it can't miss, but the cost grows with the data. Approximate search uses an index to check a small part of it, trading some recall for a lot of speed. On 50,000 random test vectors, exact took 85 ms and HNSW about 2 ms. I measure recall by comparing the index's results with exact search on real queries.

**Follow-up:** How would you set a recall target?

### How does HNSW work?

**Strong answer:** It's a graph in layers. Upper layers have few points and long links, and lower layers have more points and short links. A search starts at the top, moves towards the query, and drops down a layer when it can't get closer. `ef_search` controls how many candidates it keeps, so it's the dial between speed and recall. It's fast, but slower to build and bigger in memory than IVFFlat.

**Follow-up:** Why might you still choose IVFFlat?

### Do you always need a vector index?

**Strong answer:** No. In my project there are 24 rows, and Postgres ignores the HNSW index, because reading every row is cheaper. That gives perfect recall too. An index is worth it when exact search gets too slow for the product. I'd measure latency first, and watch filters, which behave differently with approximate indexes.

**Follow-up:** At roughly what size would you add one?

## Check yourself

### What does a recall@10 of 0.8 mean?

- [ ] 80% of answers were right — recall measures retrieval, not answers.
- [x] The index found 8 of the true 10 nearest — right: that's compared with exact search.
- [ ] The search took 80% of the time — that's speed.

### What does raising `ef_search` do?

- [x] Slower search, better recall — right: it keeps more candidates.
- [ ] Faster search, better recall — you pay for it in time.
- [ ] Rebuilds the index — it's a query-time setting.

### Why does Postgres ignore the index at 24 rows?

- [ ] The index is broken — forcing it shows it works.
- [ ] Indexes need a million rows to run — no such rule exists.
- [x] Reading every row is cheaper — right: the planner chooses the lowest cost.
