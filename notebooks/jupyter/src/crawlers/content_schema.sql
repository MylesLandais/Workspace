-- Imageboard Content Schema for Archival Analysis

CREATE TABLE IF NOT EXISTS ib_threads (
    board VARCHAR(10) NOT NULL,
    thread_id BIGINT NOT NULL,
    subject TEXT,
    replies INT DEFAULT 0,
    images INT DEFAULT 0,
    last_modified BIGINT,
    semantic_url TEXT,
    local_html_path VARCHAR(512),
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (board, thread_id),
    INDEX idx_board (board),
    INDEX idx_last_modified (last_modified)
);

CREATE TABLE IF NOT EXISTS ib_posts (
    post_id BIGINT NOT NULL,
    thread_id BIGINT NOT NULL,
    board VARCHAR(10) NOT NULL,
    name VARCHAR(255),
    comment TEXT,
    created_at TIMESTAMP NULL,
    local_image VARCHAR(512),
    sha256 VARCHAR(64),
    PRIMARY KEY (board, post_id),
    FOREIGN KEY (board, thread_id) REFERENCES ib_threads(board, thread_id) ON DELETE CASCADE,
    INDEX idx_thread (board, thread_id),
    INDEX idx_sha256 (sha256)
);

CREATE TABLE IF NOT EXISTS ib_images (
    sha256 VARCHAR(64) PRIMARY KEY,
    ext VARCHAR(10),
    width INT,
    height INT,
    fsize INT,
    original_filename TEXT,
    local_path VARCHAR(512),
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
