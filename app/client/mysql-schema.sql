-- Better Auth MySQL Schema
-- Column names must use snake_case for Better Auth compatibility
-- Use CREATE INDEX with IF NOT EXISTS for compatibility

CREATE TABLE IF NOT EXISTS `user` (
  `id` VARCHAR(255) PRIMARY KEY,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `email_verified` TINYINT(1) DEFAULT 0,
  `name` VARCHAR(255),
  `image` VARCHAR(255),
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `account` (
  `id` VARCHAR(255) PRIMARY KEY,
  `account_id` VARCHAR(255) NOT NULL,
  `user_id` VARCHAR(255) NOT NULL,
  `provider_id` VARCHAR(255) NOT NULL,
  `access_token` TEXT,
  `refresh_token` TEXT,
  `id_token` TEXT,
  `expires_at` TIMESTAMP NULL,
  `password` TEXT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `account_provider_account_id` (`provider_id`, `account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `session` (
  `id` VARCHAR(255) PRIMARY KEY,
  `expires_at` TIMESTAMP NOT NULL,
  `token` TEXT NOT NULL,
  `ip_address` VARCHAR(50),
  `user_agent` TEXT,
  `user_id` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `verification` (
  `id` VARCHAR(255) PRIMARY KEY,
  `identifier` VARCHAR(255) NOT NULL,
  `value` VARCHAR(255) NOT NULL,
  `expires_at` TIMESTAMP NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexes for performance
CREATE INDEX idx_user_email ON `user`(`email`);
CREATE INDEX idx_session_user_id ON `session`(`user_id`);
CREATE INDEX idx_session_expires_at ON `session`(`expires_at`);
CREATE INDEX idx_verification_expires_at ON `verification`(`expires_at`);
