CREATE TABLE `account` (
	`id` varchar(255) NOT NULL,
	`account_id` varchar(255) NOT NULL,
	`provider_id` varchar(255) NOT NULL,
	`user_id` varchar(255) NOT NULL,
	`access_token` text,
	`refresh_token` text,
	`id_token` text,
	`expires_at` datetime(3),
	`access_token_expires_at` datetime(3),
	`refresh_token_expires_at` datetime(3),
	`scope` text,
	`password` text,
	`created_at` datetime(3) NOT NULL,
	`updated_at` datetime(3) NOT NULL,
	CONSTRAINT `account_id` PRIMARY KEY(`id`),
	CONSTRAINT `account_provider_accountId_idx` UNIQUE(`provider_id`,`account_id`)
);
--> statement-breakpoint
CREATE TABLE `invite_code` (
	`id` varchar(255) NOT NULL,
	`code` varchar(100) NOT NULL,
	`expires_at` datetime(3) NOT NULL,
	`max_uses` tinyint,
	`used_count` tinyint NOT NULL DEFAULT 0,
	`created_by` varchar(255),
	`notes` text,
	`created_at` datetime(3) NOT NULL,
	`updated_at` datetime(3) NOT NULL,
	CONSTRAINT `invite_code_id` PRIMARY KEY(`id`),
	CONSTRAINT `invite_code_code_unique` UNIQUE(`code`)
);
--> statement-breakpoint
CREATE TABLE `session` (
	`id` varchar(255) NOT NULL,
	`expires_at` datetime(3) NOT NULL,
	`token` varchar(512) NOT NULL,
	`created_at` datetime(3) NOT NULL,
	`updated_at` datetime(3) NOT NULL,
	`ip_address` varchar(50),
	`user_agent` text,
	`user_id` varchar(255) NOT NULL,
	CONSTRAINT `session_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `user` (
	`id` varchar(255) NOT NULL,
	`name` text,
	`email` varchar(255) NOT NULL,
	`email_verified` tinyint NOT NULL DEFAULT 0,
	`image` text,
	`username` varchar(100),
	`join_date` datetime(3),
	`created_at` datetime(3) NOT NULL,
	`updated_at` datetime(3) NOT NULL,
	CONSTRAINT `user_id` PRIMARY KEY(`id`),
	CONSTRAINT `user_email_unique` UNIQUE(`email`),
	CONSTRAINT `user_username_unique` UNIQUE(`username`)
);
--> statement-breakpoint
CREATE TABLE `verification` (
	`id` varchar(255) NOT NULL,
	`identifier` varchar(255) NOT NULL,
	`value` varchar(255) NOT NULL,
	`expires_at` datetime(3) NOT NULL,
	`created_at` datetime(3) NOT NULL,
	`updated_at` datetime(3) NOT NULL,
	CONSTRAINT `verification_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `waitlist` (
	`id` varchar(255) NOT NULL,
	`email` varchar(255) NOT NULL,
	`name` varchar(255),
	`status` enum('pending','invited','joined') NOT NULL DEFAULT 'pending',
	`invite_code` varchar(255),
	`invite_sent_at` datetime(3),
	`source` varchar(100),
	`notes` text,
	`created_at` datetime(3) NOT NULL,
	`updated_at` datetime(3) NOT NULL,
	CONSTRAINT `waitlist_id` PRIMARY KEY(`id`),
	CONSTRAINT `waitlist_email_unique` UNIQUE(`email`),
	CONSTRAINT `waitlist_invite_code_unique` UNIQUE(`invite_code`)
);
--> statement-breakpoint
ALTER TABLE `account` ADD CONSTRAINT `account_user_id_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `session` ADD CONSTRAINT `session_user_id_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX `account_userId_idx` ON `account` (`user_id`);--> statement-breakpoint
CREATE INDEX `invite_code_code_idx` ON `invite_code` (`code`);--> statement-breakpoint
CREATE INDEX `invite_code_expiresAt_idx` ON `invite_code` (`expires_at`);--> statement-breakpoint
CREATE INDEX `session_userId_idx` ON `session` (`user_id`);--> statement-breakpoint
CREATE INDEX `session_expiresAt_idx` ON `session` (`expires_at`);--> statement-breakpoint
CREATE INDEX `verification_expiresAt_idx` ON `verification` (`expires_at`);--> statement-breakpoint
CREATE INDEX `waitlist_email_idx` ON `waitlist` (`email`);--> statement-breakpoint
CREATE INDEX `waitlist_status_idx` ON `waitlist` (`status`);--> statement-breakpoint
CREATE INDEX `waitlist_inviteCode_idx` ON `waitlist` (`invite_code`);