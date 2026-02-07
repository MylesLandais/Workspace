/**
 * User subscription schema for managing per-user source subscriptions.
 *
 * MySQL stores user-specific settings (notifications, priority, tags).
 * Neo4j stores relationships for efficient graph queries (crawler, feed).
 */
import { relations } from "drizzle-orm";
import {
  mysqlTable,
  text,
  datetime,
  tinyint,
  varchar,
  int,
  index,
  uniqueIndex,
  mysqlEnum,
} from "drizzle-orm/mysql-core";
import { user } from "./mysql-auth.js";

/**
 * Per-user subscription with settings.
 * Links MySQL user to Neo4j Source via sourceId.
 */
export const userSubscription = mysqlTable(
  "user_subscription",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    userId: varchar("user_id", { length: 255 })
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
    sourceId: varchar("source_id", { length: 255 }).notNull(), // Neo4j Source.id
    groupId: varchar("group_id", { length: 255 }), // Optional folder/group

    // User-specific settings
    isPaused: tinyint("is_paused").default(0).notNull(),
    notifications: mysqlEnum("notifications", ["all", "highlights", "none"])
      .default("none")
      .notNull(),
    priority: tinyint("priority").default(0).notNull(), // 0=normal, 1=high, 2=low
    tags: text("tags"), // JSON array: ["tech", "linux"]
    notes: text("notes"), // User's private notes

    // Timestamps
    addedAt: datetime("added_at", { mode: "date", fsp: 3 }).notNull(),
    lastViewedAt: datetime("last_viewed_at", { mode: "date", fsp: 3 }),
    createdAt: datetime("created_at", { mode: "date", fsp: 3 }).notNull(),
    updatedAt: datetime("updated_at", { mode: "date", fsp: 3 }).notNull(),
  },
  (table) => [
    index("usub_userId_idx").on(table.userId),
    index("usub_sourceId_idx").on(table.sourceId),
    index("usub_groupId_idx").on(table.groupId),
    uniqueIndex("usub_user_source_uniq").on(table.userId, table.sourceId),
  ],
);

/**
 * User-defined subscription folders/groups.
 * Allows users to organize their subscriptions.
 */
export const subscriptionGroup = mysqlTable(
  "subscription_group",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    userId: varchar("user_id", { length: 255 })
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
    name: varchar("name", { length: 255 }).notNull(),
    color: varchar("color", { length: 20 }), // Hex color code
    icon: varchar("icon", { length: 50 }), // Emoji or icon name
    sortOrder: int("sort_order").default(0).notNull(),
    createdAt: datetime("created_at", { mode: "date", fsp: 3 }).notNull(),
    updatedAt: datetime("updated_at", { mode: "date", fsp: 3 }).notNull(),
  },
  (table) => [
    index("subgrp_userId_idx").on(table.userId),
    uniqueIndex("subgrp_user_name_uniq").on(table.userId, table.name),
  ],
);

// Relations
export const userSubscriptionRelations = relations(
  userSubscription,
  ({ one }) => ({
    user: one(user, {
      fields: [userSubscription.userId],
      references: [user.id],
    }),
    group: one(subscriptionGroup, {
      fields: [userSubscription.groupId],
      references: [subscriptionGroup.id],
    }),
  }),
);

export const subscriptionGroupRelations = relations(
  subscriptionGroup,
  ({ one, many }) => ({
    user: one(user, {
      fields: [subscriptionGroup.userId],
      references: [user.id],
    }),
    subscriptions: many(userSubscription),
  }),
);
