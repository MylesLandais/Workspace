-- Control Plane Schema for Reddit/Social Crawler

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    department VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS targets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    target_type ENUM('subreddit', 'user', 'keyword') NOT NULL,
    value VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_crawled_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_target (target_type, value)
);

CREATE TABLE IF NOT EXISTS user_subscriptions (
    user_id INT,
    target_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, target_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES targets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crawl_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    target_id INT,
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
    items_collected INT DEFAULT 0,
    minio_path VARCHAR(512),
    error_message TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (target_id) REFERENCES targets(id)
);

-- Seed Initial Data
INSERT IGNORE INTO users (username, department) VALUES 
('researcher_1', 'Data Science'),
('researcher_2', 'Sociology');

INSERT IGNORE INTO targets (target_type, value, description) VALUES 
('subreddit', 'nixos', 'NixOS community discussions'),
('subreddit', 'dataengineering', 'Data Engineering topics'),
('subreddit', 'LocalLLaMA', 'Local LLM discussions');

INSERT IGNORE INTO user_subscriptions (user_id, target_id) 
SELECT u.id, t.id 
FROM users u, targets t 
WHERE u.username = 'researcher_1' AND t.value = 'nixos';
