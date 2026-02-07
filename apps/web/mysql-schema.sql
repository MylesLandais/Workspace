-- Better Auth MySQL Schema
-- Uses DATETIME for timestamp fields (Better Auth sends datetime strings)

CREATE TABLE IF NOT EXISTS `user` (
  `id` VARCHAR(255) PRIMARY KEY,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `email_verified` TINYINT(1) DEFAULT 0,
  `name` VARCHAR(255),
  `image` TEXT,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `account` (
  `id` VARCHAR(255) PRIMARY KEY,
  `account_id` VARCHAR(255) NOT NULL,
  `user_id` VARCHAR(255) NOT NULL,
  `provider_id` VARCHAR(255) NOT NULL,
  `access_token` TEXT,
  `refresh_token` TEXT,
  `id_token` TEXT,
  `expires_at` DATETIME(3),
  `access_token_expires_at` DATETIME(3),
  `refresh_token_expires_at` DATETIME(3),
  `scope` TEXT,
  `password` TEXT,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `account_provider_account_id` (`provider_id`, `account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `session` (
  `id` VARCHAR(255) PRIMARY KEY,
  `expires_at` DATETIME(3) NOT NULL,
  `token` VARCHAR(512) NOT NULL,
  `ip_address` VARCHAR(50),
  `user_agent` TEXT,
  `user_id` VARCHAR(255) NOT NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `session_token_unique` (`token`(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `verification` (
  `id` VARCHAR(255) PRIMARY KEY,
  `identifier` VARCHAR(255) NOT NULL,
  `value` VARCHAR(255) NOT NULL,
  `expires_at` DATETIME(3) NOT NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `waitlist` (
  `id` VARCHAR(255) PRIMARY KEY,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `name` VARCHAR(255),
  `status` ENUM('pending', 'invited', 'joined') DEFAULT 'pending',
  `invite_code` VARCHAR(255) UNIQUE,
  `invite_sent_at` DATETIME(3),
  `source` VARCHAR(100),
  `notes` TEXT,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexes for performance
CREATE INDEX idx_user_email ON `user`(`email`);
CREATE INDEX idx_session_user_id ON `session`(`user_id`);
CREATE INDEX idx_session_expires_at ON `session`(`expires_at`);
CREATE INDEX idx_account_user_id ON `account`(`user_id`);
CREATE INDEX idx_verification_expires_at ON `verification`(`expires_at`);
CREATE INDEX idx_waitlist_email ON `waitlist`(`email`);
CREATE INDEX idx_waitlist_status ON `waitlist`(`status`);
CREATE INDEX idx_waitlist_invite_code ON `waitlist`(`invite_code`);
