-- Local database for docker-compose. Safe to run repeatedly (see setup_local.py).
-- LangGraph creates its own checkpoint* tables when the API starts.

CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector: adds the VECTOR type and distance operators

-- Replaces the DynamoDB orders table. JSONB keeps orders schemaless, as they are in DynamoDB.
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    data     JSONB NOT NULL
);

-- Replaces the DynamoDB history table.
CREATE TABLE IF NOT EXISTS chat_history (
    id         BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    role       TEXT NOT NULL,
    text       TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS chat_history_session_idx ON chat_history (session_id, id);

-- Replaces the Bedrock Knowledge Base + S3 Vectors index: one row per chunk of a policy document.
CREATE TABLE IF NOT EXISTS policy_chunks (
    id           BIGSERIAL PRIMARY KEY,
    source       TEXT NOT NULL,            -- file name, used for citations
    chunk_index  INT  NOT NULL,            -- position inside the document
    content      TEXT NOT NULL,            -- the text shown to the model
    content_hash TEXT NOT NULL,            -- lets ingestion skip unchanged documents
    embedding    VECTOR(768) NOT NULL,     -- must equal the embedding model's dimensions
    UNIQUE (source, chunk_index)
);

-- HNSW = approximate nearest-neighbour index, using cosine distance (the <=> operator).
-- A few dozen rows don't need it (a full scan is faster). It is here because real corpora do.
CREATE INDEX IF NOT EXISTS policy_chunks_embedding_idx
    ON policy_chunks USING hnsw (embedding vector_cosine_ops);

-- Feature 020: accounts. Everything below is safe to run on an existing database.

CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,    -- stored lower-case
    password_hash TEXT NOT NULL,           -- Argon2id: salted and deliberately slow
    role          TEXT NOT NULL CHECK (role IN ('customer', 'support', 'admin')),
    display_name  TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- A signed-in browser. Holds a hash of the token, so a stolen table can't be replayed.
CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- Failed logins, for lockout. Keyed by email so unknown emails lock too.
CREATE TABLE IF NOT EXISTS login_attempts (
    email        TEXT NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS login_attempts_email_idx ON login_attempts (email, attempted_at);

-- Who owns each conversation. A session with no row here is visible to nobody.
CREATE TABLE IF NOT EXISTS conversations (
    session_id TEXT PRIMARY KEY,
    owner_id   BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title      TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS conversations_owner_idx ON conversations (owner_id, updated_at DESC);

-- The staff review queue. Approval rules read these stored values, never the request.
CREATE TABLE IF NOT EXISTS refund_requests (
    id               BIGSERIAL PRIMARY KEY,
    session_id       TEXT NOT NULL,
    order_id         TEXT NOT NULL,
    owner_id         BIGINT NOT NULL REFERENCES users (id),
    amount           NUMERIC(10, 2) NOT NULL,
    reason           TEXT NOT NULL DEFAULT '',
    needs_supervisor BOOLEAN NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'claimed', 'approved', 'rejected', 'cancelled')),
    reviewer_id      BIGINT REFERENCES users (id),
    note             TEXT NOT NULL DEFAULT '',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at       TIMESTAMPTZ
);
-- One open request per conversation, enforced by the database.
CREATE UNIQUE INDEX IF NOT EXISTS refund_requests_one_open_idx
    ON refund_requests (session_id) WHERE status IN ('pending', 'claimed');

ALTER TABLE orders ADD COLUMN IF NOT EXISTS owner_id BIGINT REFERENCES users (id);
CREATE INDEX IF NOT EXISTS orders_owner_idx ON orders (owner_id);

CREATE SEQUENCE IF NOT EXISTS order_numbers START 2001;  -- sample orders for new sign-ups

-- Feature 021: the shop. Filled from data/products.json by setup, which is the only source of prices.
CREATE TABLE IF NOT EXISTS products (
    id           INT PRIMARY KEY,           -- fixed in the file, because guest carts store it
    slug         TEXT NOT NULL UNIQUE,      -- the product's URL and its illustration's file name
    category     TEXT NOT NULL,
    name         TEXT NOT NULL,
    price        NUMERIC(10, 2) NOT NULL CHECK (price > 0),
    description  TEXT NOT NULL,
    specs        JSONB NOT NULL,
    rating       NUMERIC(2, 1) NOT NULL,
    rating_count INT NOT NULL,
    added_at     DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS products_category_idx ON products (category);

-- Signed-in carts. No price column: a cart can't hold one, so it can't be tampered with.
CREATE TABLE IF NOT EXISTS cart_items (
    user_id    BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products (id),
    quantity   INT NOT NULL CHECK (quantity BETWEEN 1 AND 10),
    PRIMARY KEY (user_id, product_id)
);
