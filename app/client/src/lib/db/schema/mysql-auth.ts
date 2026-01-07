/**
 * Authentication database schema for Better Auth (MySQL).
 *
 * Uses snake_case column names to match MySQL physical schema
 * and Better Auth's expected column naming.
 */
import { relations } from "drizzle-orm";
import { mysqlTable, text, datetime, tinyint, varchar, index, uniqueIndex, mysqlEnum } from "drizzle-orm/mysql-core";

export const user = mysqlTable("user", {
  id: varchar("id", { length: 255 }).primaryKey(),
  name: text("name"),
  email: varchar("email", { length: 255 }).notNull().unique(),
  emailVerified: tinyint("email_verified").default(0).notNull(),
  image: text("image"),
  username: varchar("username", { length: 100 }).unique(),
  bio: text("bio"),
  location: varchar("location", { length: 255 }),
  website: varchar("website", { length: 500 }),
  company: varchar("company", { length: 255 }),
  profilePublic: tinyint("profile_public").default(0).notNull(),
  joinDate: datetime("join_date", { mode: "date", fsp: 3 }),
  createdAt: datetime("created_at", { mode: "date", fsp: 3 }).notNull(),
  updatedAt: datetime("updated_at", { mode: "date", fsp: 3 }).notNull(),
});

export const session = mysqlTable(
  "session",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    expiresAt: datetime("expires_at", { mode: "date", fsp: 3 }).notNull(),
    token: varchar("token", { length: 512 }).notNull(),
    createdAt: datetime("created_at", { mode: "date", fsp: 3 }).notNull(),
    updatedAt: datetime("updated_at", { mode: "date", fsp: 3 }).notNull(),
    ipAddress: varchar("ip_address", { length: 50 }),
    userAgent: text("user_agent"),
    userId: varchar("user_id", { length: 255 })
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
  },
  (table) => [
    index("session_userId_idx").on(table.userId),
    index("session_expiresAt_idx").on(table.expiresAt),
  ],
);

export const account = mysqlTable(
  "account",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    accountId: varchar("account_id", { length: 255 }).notNull(),
    providerId: varchar("provider_id", { length: 255 }).notNull(),
    userId: varchar("user_id", { length: 255 })
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
    accessToken: text("access_token"),
    refreshToken: text("refresh_token"),
    idToken: text("id_token"),
    expiresAt: datetime("expires_at", { mode: "date", fsp: 3 }),
    accessTokenExpiresAt: datetime("access_token_expires_at", { mode: "date", fsp: 3 }),
    refreshTokenExpiresAt: datetime("refresh_token_expires_at", { mode: "date", fsp: 3 }),
    scope: text("scope"),
    password: text("password"),
    createdAt: datetime("created_at", { mode: "date", fsp: 3 }).notNull(),
    updatedAt: datetime("updated_at", { mode: "date", fsp: 3 }).notNull(),
  },
  (table) => [
    index("account_userId_idx").on(table.userId),
    uniqueIndex("account_provider_accountId_idx").on(table.providerId, table.accountId),
  ],
);

export const verification = mysqlTable(
  "verification",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    identifier: varchar("identifier", { length: 255 }).notNull(),
    value: varchar("value", { length: 255 }).notNull(),
    expiresAt: datetime("expires_at", { mode: "date", fsp: 3 }).notNull(),
    createdAt: datetime("created_at", { mode: "date", fsp: 3 }).notNull(),
    updatedAt: datetime("updated_at", { mode: "date", fsp: 3 }).notNull(),
  },
  (table) => [index("verification_expiresAt_idx").on(table.expiresAt)],
);

export const userRelations = relations(user, ({ many }) => ({
  sessions: many(session),
  accounts: many(account),
}));

export const sessionRelations = relations(session, ({ one }) => ({
  user: one(user, {
    fields: [session.userId],
    references: [user.id],
  }),
}));

export const accountRelations = relations(account, ({ one }) => ({
  user: one(user, {
    fields: [account.userId],
    references: [user.id],
  }),
}));

export const waitlist = mysqlTable(
  "waitlist",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    email: varchar("email", { length: 255 }).notNull().unique(),
    name: varchar("name", { length: 255 }),
    status: mysqlEnum("status", ["pending", "invited", "joined"]).default("pending").notNull(),
    inviteCode: varchar("invite_code", { length: 255 }).unique(),
    inviteSentAt: datetime("invite_sent_at", { mode: "date", fsp: 3 }),
    source: varchar("source", { length: 100 }),
    notes: text("notes"),
    createdAt: datetime("created_at", { mode: "date", fsp: 3 }).notNull(),
    updatedAt: datetime("updated_at", { mode: "date", fsp: 3 }).notNull(),
  },
  (table) => [
    index("waitlist_email_idx").on(table.email),
    index("waitlist_status_idx").on(table.status),
    index("waitlist_inviteCode_idx").on(table.inviteCode),
  ],
);

export const inviteCode = mysqlTable(
  "invite_code",
  {
    id: varchar("id", { length: 255 }).primaryKey(),
    code: varchar("code", { length: 100 }).notNull().unique(),
    expiresAt: datetime("expires_at", { mode: "date", fsp: 3 }).notNull(),
    maxUses: tinyint("max_uses"),
    usedCount: tinyint("used_count").default(0).notNull(),
    createdBy: varchar("created_by", { length: 255 }),
    notes: text("notes"),
    createdAt: datetime("created_at", { mode: "date", fsp: 3 }).notNull(),
    updatedAt: datetime("updated_at", { mode: "date", fsp: 3 }).notNull(),
  },
  (table) => [
    index("invite_code_code_idx").on(table.code),
    index("invite_code_expiresAt_idx").on(table.expiresAt),
  ],
);
