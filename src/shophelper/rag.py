"""RAG on the local stack: the pipeline a Bedrock Knowledge Base runs for you on AWS.

    INGEST (once)   markdown -> chunks -> embeddings -> Postgres (pgvector)
    QUERY (per ask) question -> embedding -> nearest chunks -> returned to the agent

Full walkthrough: docs/learn/04-rag.md
"""

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

from shophelper import db
from shophelper.config import get_settings

POLICY_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "policies"
MAX_CHUNK_CHARS = 350

# nomic-embed-text was trained with these prefixes. Questions and documents are different
# kinds of text, and the prefix tells the model which one it is embedding.
DOCUMENT_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "


def chunk_markdown(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split on line boundaries so a rule is never cut in half, packing lines up to max_chars.

    Every chunk starts with the document title. On its own, "within 30 days" says nothing
    about what it applies to; "# Refund Policy" gives the embedding that context.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0] if lines and lines[0].startswith("#") else ""
    body = lines[1:] if title else lines

    chunks: list[str] = []
    current: list[str] = []
    for line in body:
        if current and len("\n".join([title, *current, line])) > max_chars:
            chunks.append("\n".join([title, *current]).strip())
            current = []
        current.append(line)
    if current:
        chunks.append("\n".join([title, *current]).strip())
    return chunks


@lru_cache
def _client():
    from openai import OpenAI

    s = get_settings()
    return OpenAI(base_url=s.llm_base_url, api_key=s.llm_api_key)


def embed(texts: list[str], prefix: str) -> list[list[float]]:
    resp = _client().embeddings.create(
        model=get_settings().embedding_model, input=[prefix + t for t in texts]
    )
    return [item.embedding for item in resp.data]


def ingest(policy_dir: Path = POLICY_DIR) -> dict[str, int]:
    """Embed every policy document. Unchanged documents are skipped, using a content hash."""
    from pgvector import Vector

    stats = {"documents": 0, "skipped": 0, "chunks": 0}
    paths = sorted(policy_dir.glob("*.md"))
    with db.connect() as conn:
        for path in paths:
            text = path.read_text(encoding="utf-8")
            digest = hashlib.sha256(text.encode()).hexdigest()
            row = conn.execute(
                "SELECT content_hash FROM policy_chunks WHERE source = %s LIMIT 1", (path.name,)
            ).fetchone()
            if row and row["content_hash"] == digest:
                stats["skipped"] += 1
                continue

            chunks = chunk_markdown(text)
            vectors = embed(chunks, DOCUMENT_PREFIX)
            conn.execute("DELETE FROM policy_chunks WHERE source = %s", (path.name,))
            for index, (content, vector) in enumerate(zip(chunks, vectors, strict=True)):
                conn.execute(
                    "INSERT INTO policy_chunks (source, chunk_index, content, content_hash, embedding) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (path.name, index, content, digest, Vector(vector)),
                )
            stats["documents"] += 1
            stats["chunks"] += len(chunks)

        # A policy file was deleted: its chunks must not keep answering questions.
        conn.execute(
            "DELETE FROM policy_chunks WHERE NOT (source = ANY(%s))", ([p.name for p in paths],)
        )
    return stats


def search(query: str, top_k: int = 4) -> list[dict[str, Any]]:
    """Nearest chunks to the query. `<=>` is cosine distance, so score = 1 - distance."""
    from pgvector import Vector

    vector = Vector(embed([query], QUERY_PREFIX)[0])
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT source, chunk_index, content AS text, 1 - (embedding <=> %s) AS score "
            "FROM policy_chunks ORDER BY embedding <=> %s LIMIT %s",
            (vector, vector, top_k),
        ).fetchall()
    return [{**r, "score": round(float(r["score"]), 3)} for r in rows]
