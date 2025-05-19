-- migrations/init_pgvector.sql

-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 벡터 저장용 document_chunks 테이블 생성
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES pdf_files(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- 빠른 문서 조회를 위한 인덱스 추가
    CONSTRAINT unique_chunk_per_document UNIQUE (document_id, chunk_index)
);

-- 효율적인 유사도 검색을 위한 HNSW 인덱스 생성
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
ON document_chunks
USING ivfflat (embedding vector_l2_ops)
WITH (lists = 100);

-- 유사도 검색 함수 생성
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector,
    document_id INTEGER,
    limit_val INTEGER DEFAULT 5
)
RETURNS TABLE (
    id INTEGER,
    document_id INTEGER,
    chunk_index INTEGER,
    text TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.chunk_index,
        dc.text,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE
        dc.document_id = document_id
        AND dc.embedding IS NOT NULL
    ORDER BY dc.embedding <=> query_embedding
    LIMIT limit_val;
END;
$$;