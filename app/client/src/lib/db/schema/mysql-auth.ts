/**
 * Authentication database schema for Better Auth (MySQL).
 * 
 * Note: Uses snake_case column names to match MySQL physical schema
 * and Better Auth's expected column naming.
 */
import { relations } from "drizzle-orm";
import { mysqlTable, text, int, tinyint, varchar, index } from "drizzle-orm/mysql-core";

export const user = mysqlTable("user", {
  id: varchar("id", { length: 255 }).primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  emailVerified: tinyint("email_verified", {
    name: "email_verified",
    mode: "boolean"
  })
    .default(false)
    .notNull(),
  image: text("image"),
  createdAt: int("created_at", {
    name: "created_at",
    mode: "timestamp"
  }).notNull(),
  updatedAt: int("updated_at", {
    name: "updated_at",
    mode: "timestamp"
  })
    .$onUpdate(() => new Date())
    .notNull(),
});

export const session = mysqlTable(
  "session",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    expiresAt: int("expires_at", {
      name: "expires_at",
      mode: "timestamp"
    }).notNull(),
    token: text("token").notNull(),
    createdAt: int("created_at", {
      name: "created_at",
      mode: "timestamp"
    }).notNull(),
    updatedAt: int("updated_at", {
      name: "updated_at",
      mode: "timestamp"
    })
      .$onUpdate(() => new Date())
      .notNull(),
    ipAddress: text("ip_address"),
    userAgent: text("user_agent"),
    userId: varchar("user_id", {
      name: "user_id",
      length: 255
    })
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
  },
  (table) => [index("session_userId_idx").on(table.userId)],
);

export const account = mysqlTable(
  "account",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    account_id: varchar("account_id", { length: 255 }).notNull(),
    provider_id: varchar("provider_id", { length: 255 }).notNull(),
    user_id: varchar("user_id", { length: 255 })
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
    access_token: text("access_token"),
    refresh_token: text("refresh_token"),
    id_token: text("id_token"),
    expires_at: int("expires_at", { mode: "timestamp" }),
    password: text("password"),
    created_at: int("created_at", { mode: "timestamp" }).notNull(),
    updated_at: int("updated_at", { mode: "timestamp" })
      .$onUpdate(() => new Date())
      .notNull(),
  },
  (table) => [
    index("account_user_id_idx").on(table.user_id),
    index("account_provider_account_id_idx").on(table.provider_id, table.account_id),
  ],
);

export const verification = mysqlTable(
  "verification",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    identifier: text("identifier").notNull(),
    value: text("value").notNull(),
    expires_at: int("expires_at", { mode: "timestamp" }).notNull(),
    created_at: int("created_at", { mode: "timestamp" }).notNull(),
    updated_at: int("updated_at", { mode: "timestamp" })
      .$onUpdate(() => new Date())
      .notNull(),
  },
  (table) => [index("verification_expires_at_idx").on(table.expires_at)],
);

export const userRelations = relations(user, ({ many }) => ({
  sessions: many(session),
  accounts: many(account),
}));

export const sessionRelations = relations(session, ({ one }) => ({
  user: one(user, {
    fields: [session.user_id],
    references: [user.id],
  }),
}));

export const accountRelations = relations(account, ({ one }) => ({
  user: one(user, {
    fields: [account.user_id],
    references: [user.id],
  }),
}));
