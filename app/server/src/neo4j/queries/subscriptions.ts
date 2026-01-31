/**
 * Neo4j subscription queries for efficient graph-based operations.
 *
 * Handles User-Source relationships for:
 * - Subscription management (subscribe/unsubscribe)
 * - Crawler queries (sources needing sync)
 * - Feed generation (user's subscribed sources)
 */
import { getSession } from "../driver.js";

export interface SourceInfo {
  id: string;
  name: string;
  sourceType: string;
  subredditName?: string;
  youtubeChannelHandle?: string;
  lastSynced: string | null;
}

export interface SubscriptionResult {
  sourceId: string;
  userId: string;
  addedAt: string;
}

export interface CrawlerSource {
  sourceId: string;
  identifier: string; // subreddit_name, youtube_channel_handle, etc.
  sourceType: string;
  subscriberCount: number;
  lastSynced: string | null;
}

/**
 * Find or create a Source node by type and identifier.
 * Deduplicates sources by their unique type+identifier combination.
 */
export async function findOrCreateSource(
  sourceType: string,
  identifier: string,
  metadata?: {
    name?: string;
    iconUrl?: string;
    description?: string;
  },
): Promise<SourceInfo> {
  const session = getSession();
  try {
    const id = crypto.randomUUID();
    const identifierField = getIdentifierField(sourceType);

    const query = `
      MERGE (s:Source {source_type: $sourceType, ${identifierField}: $identifier})
      ON CREATE SET
        s.id = $id,
        s.name = coalesce($name, $identifier),
        s.icon_url = $iconUrl,
        s.description = $description,
        s.is_enabled = true,
        s.is_paused = false,
        s.media_count = 0,
        s.created_at = datetime()
      ON MATCH SET
        s.icon_url = coalesce($iconUrl, s.icon_url),
        s.description = coalesce($description, s.description),
        s.updated_at = datetime()
      RETURN s
    `;

    const result = await session.run(query, {
      id,
      sourceType: sourceType.toUpperCase(),
      identifier: identifier.toLowerCase(),
      name: metadata?.name || null,
      iconUrl: metadata?.iconUrl || null,
      description: metadata?.description || null,
    });

    const source = result.records[0].get("s").properties;
    return mapSourceInfo(source);
  } finally {
    await session.close();
  }
}

/**
 * Create a SUBSCRIBES_TO relationship between User and Source.
 * Idempotent: won't create duplicate relationships.
 */
export async function createSubscription(
  userId: string,
  sourceId: string,
): Promise<SubscriptionResult | null> {
  const session = getSession();
  try {
    // Ensure User node exists (synced from MySQL)
    const query = `
      MERGE (u:User {id: $userId})
      WITH u
      MATCH (s:Source {id: $sourceId})
      MERGE (u)-[r:SUBSCRIBES_TO]->(s)
      ON CREATE SET r.added_at = datetime()
      RETURN u.id AS userId, s.id AS sourceId, r.added_at AS addedAt
    `;

    const result = await session.run(query, { userId, sourceId });

    if (result.records.length === 0) {
      return null;
    }

    const record = result.records[0];
    return {
      userId: record.get("userId"),
      sourceId: record.get("sourceId"),
      addedAt: formatDateTime(record.get("addedAt")),
    };
  } finally {
    await session.close();
  }
}

/**
 * Remove SUBSCRIBES_TO relationship between User and Source.
 */
export async function removeSubscription(
  userId: string,
  sourceId: string,
): Promise<boolean> {
  const session = getSession();
  try {
    const query = `
      MATCH (u:User {id: $userId})-[r:SUBSCRIBES_TO]->(s:Source {id: $sourceId})
      DELETE r
      RETURN count(r) AS deleted
    `;

    const result = await session.run(query, { userId, sourceId });
    const deleted = result.records[0]?.get("deleted")?.toNumber() || 0;

    return deleted > 0;
  } finally {
    await session.close();
  }
}

/**
 * Check if a user is subscribed to a source.
 */
export async function isSubscribed(
  userId: string,
  sourceId: string,
): Promise<boolean> {
  const session = getSession();
  try {
    const query = `
      MATCH (u:User {id: $userId})-[:SUBSCRIBES_TO]->(s:Source {id: $sourceId})
      RETURN count(s) > 0 AS subscribed
    `;

    const result = await session.run(query, { userId, sourceId });
    return result.records[0]?.get("subscribed") || false;
  } finally {
    await session.close();
  }
}

/**
 * Get all sources a user is subscribed to.
 */
export async function getUserSubscribedSources(
  userId: string,
  options?: {
    sourceType?: string;
    limit?: number;
    offset?: number;
  },
): Promise<SourceInfo[]> {
  const session = getSession();
  try {
    let query = `
      MATCH (u:User {id: $userId})-[r:SUBSCRIBES_TO]->(s:Source)
    `;

    const params: Record<string, unknown> = { userId };

    if (options?.sourceType) {
      query += ` WHERE s.source_type = $sourceType`;
      params.sourceType = options.sourceType.toUpperCase();
    }

    query += `
      RETURN s
      ORDER BY r.added_at DESC
    `;

    if (options?.limit) {
      query += ` SKIP $offset LIMIT $limit`;
      params.offset = options.offset || 0;
      params.limit = options.limit;
    }

    const result = await session.run(query, params);

    return result.records.map((record) => {
      const source = record.get("s").properties;
      return mapSourceInfo(source);
    });
  } finally {
    await session.close();
  }
}

/**
 * Get source IDs for a user's subscriptions.
 * Lightweight query for joining with MySQL subscription settings.
 */
export async function getUserSubscribedSourceIds(
  userId: string,
): Promise<string[]> {
  const session = getSession();
  try {
    const query = `
      MATCH (u:User {id: $userId})-[:SUBSCRIBES_TO]->(s:Source)
      RETURN s.id AS sourceId
    `;

    const result = await session.run(query, { userId });
    return result.records.map((record) => record.get("sourceId"));
  } finally {
    await session.close();
  }
}

/**
 * Get sources that need crawling (have active subscribers, stale sync).
 * Used by the crawler to prioritize sources.
 */
export async function getSourcesForCrawler(options: {
  sourceType: string;
  staleMinutes?: number;
  limit?: number;
}): Promise<CrawlerSource[]> {
  const session = getSession();
  try {
    const staleMinutes = options.staleMinutes || 60;
    const limit = options.limit || 100;

    const query = `
      MATCH (s:Source {source_type: $sourceType})<-[:SUBSCRIBES_TO]-(u:User)
      WHERE s.is_enabled <> false
        AND s.is_paused <> true
        AND (
          s.last_synced IS NULL
          OR datetime() - s.last_synced > duration({minutes: $staleMinutes})
        )
      WITH s, count(u) AS subscriberCount
      RETURN
        s.id AS sourceId,
        CASE s.source_type
          WHEN 'REDDIT' THEN s.subreddit_name
          WHEN 'YOUTUBE' THEN s.youtube_channel_handle
          WHEN 'RSS' THEN s.rss_url
          ELSE s.name
        END AS identifier,
        s.source_type AS sourceType,
        subscriberCount,
        s.last_synced AS lastSynced
      ORDER BY s.last_synced ASC NULLS FIRST
      LIMIT $limit
    `;

    const result = await session.run(query, {
      sourceType: options.sourceType.toUpperCase(),
      staleMinutes,
      limit,
    });

    return result.records.map((record) => ({
      sourceId: record.get("sourceId"),
      identifier: record.get("identifier"),
      sourceType: record.get("sourceType"),
      subscriberCount: record.get("subscriberCount").toNumber(),
      lastSynced: formatDateTime(record.get("lastSynced")),
    }));
  } finally {
    await session.close();
  }
}

/**
 * Mark a source as synced after crawler processes it.
 */
export async function markSourceSynced(
  sourceId: string,
  metadata?: {
    mediaCount?: number;
    error?: string;
  },
): Promise<void> {
  const session = getSession();
  try {
    let setClauses = ["s.last_synced = datetime()"];

    if (metadata?.mediaCount !== undefined) {
      setClauses.push("s.media_count = $mediaCount");
    }
    if (metadata?.error) {
      setClauses.push("s.last_sync_error = $error");
    } else {
      setClauses.push("s.last_sync_error = null");
    }

    const query = `
      MATCH (s:Source {id: $sourceId})
      SET ${setClauses.join(", ")}
    `;

    await session.run(query, {
      sourceId,
      mediaCount: metadata?.mediaCount || 0,
      error: metadata?.error || null,
    });
  } finally {
    await session.close();
  }
}

/**
 * Get subscriber count for a source.
 */
export async function getSourceSubscriberCount(
  sourceId: string,
): Promise<number> {
  const session = getSession();
  try {
    const query = `
      MATCH (s:Source {id: $sourceId})<-[:SUBSCRIBES_TO]-(u:User)
      RETURN count(u) AS count
    `;

    const result = await session.run(query, { sourceId });
    return result.records[0]?.get("count")?.toNumber() || 0;
  } finally {
    await session.close();
  }
}

/**
 * Bulk subscribe user to multiple sources.
 * Efficient batch operation for imports.
 */
export async function bulkSubscribe(
  userId: string,
  sourceIds: string[],
): Promise<{ subscribed: number; failed: number }> {
  const session = getSession();
  try {
    const query = `
      MERGE (u:User {id: $userId})
      WITH u
      UNWIND $sourceIds AS sourceId
      MATCH (s:Source {id: sourceId})
      MERGE (u)-[r:SUBSCRIBES_TO]->(s)
      ON CREATE SET r.added_at = datetime()
      RETURN count(r) AS subscribed
    `;

    const result = await session.run(query, { userId, sourceIds });
    const subscribed = result.records[0]?.get("subscribed")?.toNumber() || 0;

    return {
      subscribed,
      failed: sourceIds.length - subscribed,
    };
  } finally {
    await session.close();
  }
}

/**
 * Find source by type and identifier.
 */
export async function findSourceByIdentifier(
  sourceType: string,
  identifier: string,
): Promise<SourceInfo | null> {
  const session = getSession();
  try {
    const identifierField = getIdentifierField(sourceType);

    const query = `
      MATCH (s:Source {source_type: $sourceType, ${identifierField}: $identifier})
      RETURN s
    `;

    const result = await session.run(query, {
      sourceType: sourceType.toUpperCase(),
      identifier: identifier.toLowerCase(),
    });

    if (result.records.length === 0) {
      return null;
    }

    const source = result.records[0].get("s").properties;
    return mapSourceInfo(source);
  } finally {
    await session.close();
  }
}

// Helper functions

function getIdentifierField(sourceType: string): string {
  switch (sourceType.toUpperCase()) {
    case "REDDIT":
      return "subreddit_name";
    case "YOUTUBE":
      return "youtube_channel_handle";
    case "TWITTER":
      return "twitter_handle";
    case "INSTAGRAM":
      return "instagram_handle";
    case "TIKTOK":
      return "tiktok_handle";
    case "RSS":
      return "rss_url";
    default:
      return "name";
  }
}

function mapSourceInfo(source: Record<string, unknown>): SourceInfo {
  return {
    id: source.id as string,
    name: source.name as string,
    sourceType: ((source.source_type as string) || "REDDIT").toUpperCase(),
    subredditName: source.subreddit_name as string | undefined,
    youtubeChannelHandle: source.youtube_channel_handle as string | undefined,
    lastSynced: formatDateTime(source.last_synced),
  };
}

function formatDateTime(value: unknown): string | null {
  if (!value) return null;
  if (typeof value === "string") return value;
  // Neo4j DateTime object
  if (typeof value === "object" && value !== null && "toString" in value) {
    return new Date(
      (value as { toString: () => string }).toString(),
    ).toISOString();
  }
  return null;
}
