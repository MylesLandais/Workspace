-- Consolidated Archiver Schema for PostgreSQL
-- Convergence of MySQL Content, MySQL Control, and Neo4j Graph logic

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;

-- Set up search path for Apache AGE
-- This should be done per session or globally
-- SET search_path = ag_catalog, "$user", public;

-- Schema for Imageboard Content
CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.threads (
    board VARCHAR(10) NOT NULL,
    thread_id BIGINT NOT NULL,
    subject TEXT,
    replies INT DEFAULT 0,
    images INT DEFAULT 0,
    last_modified BIGINT,
    semantic_url TEXT,
    local_html_path VARCHAR(512),
    discovered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (board, thread_id)
);

CREATE TABLE IF NOT EXISTS content.posts (
    post_id BIGINT NOT NULL,
    thread_id BIGINT NOT NULL,
    board VARCHAR(10) NOT NULL,
    name VARCHAR(255),
    comment TEXT,
    created_at TIMESTAMPTZ NULL,
    local_image VARCHAR(512),
    sha256 VARCHAR(64),
    PRIMARY KEY (board, post_id),
    FOREIGN KEY (board, thread_id) REFERENCES content.threads(board, thread_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS content.images (
    sha256 VARCHAR(64) PRIMARY KEY,
    ext VARCHAR(10),
    width INT,
    height INT,
    fsize INT,
    original_filename TEXT,
    local_path VARCHAR(512),
    discovered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    -- pgVector embedding (e.g., CLIP-ViT-B/32 uses 512 dimensions)
    embedding vector(512)
);

-- Indexing for performance
CREATE INDEX idx_threads_last_modified ON content.threads(last_modified);
CREATE INDEX idx_posts_thread ON content.posts(board, thread_id);
CREATE INDEX idx_posts_sha256 ON content.posts(sha256);

-- Schema for Control Plane
CREATE SCHEMA IF NOT EXISTS control;

CREATE TABLE IF NOT EXISTS control.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    department VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS control.targets (
    id SERIAL PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL, -- subreddit, user, keyword, board
    value VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_crawled_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (target_type, value)
);

CREATE TABLE IF NOT EXISTS control.user_subscriptions (
    user_id INT REFERENCES control.users(id) ON DELETE CASCADE,
    target_id INT REFERENCES control.targets(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, target_id)
);

-- Curation Table (Refactored from MySQL discussion)
CREATE TABLE IF NOT EXISTS control.curation (
    id SERIAL PRIMARY KEY,
    board VARCHAR(10) NOT NULL,
    item_id BIGINT NOT NULL,
    item_type VARCHAR(20) NOT NULL, -- thread, post
    action VARCHAR(20) DEFAULT 'soft_delete', -- soft_delete, flag, sticky
    reason VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_curation_item ON control.curation (board, item_id);
