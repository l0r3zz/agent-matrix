-- =============================================================================
-- Open Brain Schema for PostgreSQL 16 + pgvector
-- Replaces: Supabase table creation, search function, RLS, grants
-- =============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main thoughts table
CREATE TABLE IF NOT EXISTS thoughts (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    metadata    JSONB DEFAULT '{}'::JSONB,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- Index for fast vector similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS thoughts_embedding_idx
    ON thoughts USING hnsw (embedding vector_cosine_ops);

-- Index for JSONB metadata filtering
CREATE INDEX IF NOT EXISTS thoughts_metadata_idx
    ON thoughts USING gin (metadata);

-- Index for date-range queries
CREATE INDEX IF NOT EXISTS thoughts_created_at_idx
    ON thoughts (created_at DESC);

-- Auto-update the updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS thoughts_updated_at ON thoughts;
CREATE TRIGGER thoughts_updated_at
    BEFORE UPDATE ON thoughts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- Semantic search function (replaces Supabase's match_thoughts RPC)
-- =============================================================================
-- Usage from Node: SELECT * FROM match_thoughts($1::vector, $2::float, $3::int, $4::jsonb)
CREATE OR REPLACE FUNCTION match_thoughts(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    filter JSONB DEFAULT '{}'::JSONB
)
RETURNS TABLE (
    id          UUID,
    content     TEXT,
    metadata    JSONB,
    similarity  FLOAT,
    created_at  TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.content,
        t.metadata,
        (1 - (t.embedding <=> query_embedding))::FLOAT AS similarity,
        t.created_at
    FROM thoughts t
    WHERE (1 - (t.embedding <=> query_embedding)) > match_threshold
      AND (filter = '{}'::JSONB OR t.metadata @> filter)
    ORDER BY t.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
