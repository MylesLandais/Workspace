import { getSession } from '../driver.js';

export interface Source {
  id: string;
  name: string;
  subredditName?: string;
  sourceType: string;
  youtubeHandle?: string;
  twitterHandle?: string;
  instagramHandle?: string;
  tiktokHandle?: string;
  url?: string;
  rssUrl?: string;
  iconUrl?: string;
  description?: string;
  entityId?: string;
  entityName?: string;
  group: string;
  groupId?: string;
  tags: string[];
  isPaused: boolean;
  isEnabled: boolean;
  isActive: boolean;
  lastSynced: string | null;
  mediaCount: number;
  storiesPerMonth: number;
  readsPerMonth: number;
  health: string;
}

export interface SourceFilters {
  groupId?: string;
  sourceType?: string;
  activity?: 'ALL' | 'ACTIVE' | 'INACTIVE' | 'PAUSED';
  searchQuery?: string;
}

export interface CreateSourceInput {
  name: string;
  sourceType: string;
  url?: string;
  subredditName?: string;
  youtubeHandle?: string;
  twitterHandle?: string;
  instagramHandle?: string;
  tiktokHandle?: string;
  groupId?: string;
  description?: string;
}

export interface UpdateSourceInput {
  name?: string;
  description?: string;
  groupId?: string;
  isPaused?: boolean;
  isEnabled?: boolean;
}

export async function getSources(groupId?: string): Promise<Source[]> {
  const session = getSession();
  try {
    let query = `
      MATCH (s:Source)
      OPTIONAL MATCH (s)-[:USING_RULE]->(r:IngestRule)
      OPTIONAL MATCH (fg:FeedGroup)-[:CONTAINS]->(s)
      OPTIONAL MATCH (e:Entity)-[:HAS_SOURCE]->(s)
    `;

    const params: any = {};

    if (groupId) {
      query += ` WHERE fg.id = $groupId`;
      params.groupId = groupId;
    }

    query += `
      RETURN s, r, fg.name AS groupName, e.id AS entityId, e.name AS entityName
      ORDER BY s.name
    `;

    const result = await session.run(query, params);

    return result.records.map((record) => {
      const source = record.get('s').properties;
      const groupName = record.get('groupName') || 'Uncategorized';
      const entityId = record.get('entityId');
      const entityName = record.get('entityName');
      return mapSourceRecord(source, groupName, entityId, entityName);
    });
  } finally {
    await session.close();
  }
}

function mapSourceRecord(
  source: any,
  groupName: string,
  entityId?: string,
  entityName?: string,
  groupId?: string
): Source {
  const lastSynced = source.last_synced
    ? new Date(source.last_synced.toString()).toISOString()
    : null;

  let health = 'red';
  if (lastSynced) {
    const hoursAgo =
      (Date.now() - new Date(lastSynced).getTime()) / (1000 * 60 * 60);
    if (hoursAgo < 1) health = 'green';
    else if (hoursAgo < 24) health = 'yellow';
  }

  const isPaused = source.is_paused || false;
  const isEnabled = source.is_enabled !== false;
  const isActive = isEnabled && !isPaused && health !== 'red';

  return {
    id: source.id,
    name: source.name,
    subredditName: source.subreddit_name,
    sourceType: source.source_type || 'REDDIT',
    youtubeHandle: source.youtube_channel_handle,
    twitterHandle: source.twitter_handle,
    instagramHandle: source.instagram_handle,
    tiktokHandle: source.tiktok_handle,
    url: source.url,
    rssUrl: source.rss_url,
    iconUrl: source.icon_url,
    description: source.description,
    entityId: entityId || undefined,
    entityName: entityName || undefined,
    group: groupName,
    groupId: groupId || undefined,
    tags: source.tags || [],
    isPaused,
    isEnabled,
    isActive,
    lastSynced,
    mediaCount: source.media_count || 0,
    storiesPerMonth: source.stories_per_month || 0,
    readsPerMonth: source.reads_per_month || 0,
    health,
  };
}

export async function getFeedGroups(): Promise<Array<{ id: string; name: string }>> {
  const session = getSession();
  try {
    const query = `
      MATCH (fg:FeedGroup)
      RETURN fg.id AS id, fg.name AS name
      ORDER BY fg.name
    `;

    const result = await session.run(query);

    if (result.records.length === 0) {
      const defaultGroup = await createDefaultFeedGroup();
      return [defaultGroup];
    }

    return result.records.map((record) => ({
      id: record.get('id'),
      name: record.get('name'),
    }));
  } finally {
    await session.close();
  }
}

async function createDefaultFeedGroup(): Promise<{ id: string; name: string }> {
  const session = getSession();
  try {
    const id = crypto.randomUUID();
    const query = `
      CREATE (fg:FeedGroup {
        id: $id,
        name: $name,
        created_at: datetime()
      })
      RETURN fg.id AS id, fg.name AS name
    `;

    const result = await session.run(query, {
      id,
      name: 'All',
    });

    return {
      id: result.records[0].get('id'),
      name: result.records[0].get('name'),
    };
  } finally {
    await session.close();
  }
}

export async function searchSubreddits(query: string): Promise<Array<{
  name: string;
  displayName: string;
  subscriberCount: number;
  description: string;
  iconUrl?: string;
  isSubscribed: boolean;
}>> {
  const session = getSession();
  try {
    const searchQuery = `
      MATCH (s:Subreddit)
      WHERE s.name CONTAINS $query OR s.display_name CONTAINS $query
      OPTIONAL MATCH (source:Source {subreddit_name: s.name})
      RETURN s, 
        CASE WHEN source IS NOT NULL THEN true ELSE false END AS isSubscribed
      LIMIT 20
    `;

    const result = await session.run(searchQuery, { query: query.toLowerCase() });

    return result.records.map((record) => {
      const subreddit = record.get('s').properties;
      const isSubscribed = record.get('isSubscribed');

      return {
        name: subreddit.name,
        displayName: subreddit.display_name || subreddit.name,
        subscriberCount: subreddit.subscribers || 0,
        description: subreddit.description || '',
        iconUrl: subreddit.icon_url,
        isSubscribed,
      };
    });
  } finally {
    await session.close();
  }
}

/**
 * Get sources with filtering support
 */
export async function getUserSources(filters?: SourceFilters): Promise<Source[]> {
  const session = getSession();
  try {
    let query = `
      MATCH (s:Source)
      OPTIONAL MATCH (fg:FeedGroup)-[:CONTAINS]->(s)
      OPTIONAL MATCH (e:Entity)-[:HAS_SOURCE]->(s)
    `;

    const whereClauses: string[] = [];
    const params: Record<string, any> = {};

    if (filters?.groupId) {
      whereClauses.push('fg.id = $groupId');
      params.groupId = filters.groupId;
    }

    if (filters?.sourceType) {
      whereClauses.push('s.source_type = $sourceType');
      params.sourceType = filters.sourceType;
    }

    if (filters?.searchQuery) {
      whereClauses.push('(toLower(s.name) CONTAINS toLower($searchQuery) OR toLower(s.subreddit_name) CONTAINS toLower($searchQuery))');
      params.searchQuery = filters.searchQuery;
    }

    if (filters?.activity) {
      switch (filters.activity) {
        case 'ACTIVE':
          whereClauses.push('s.is_paused = false AND s.is_enabled <> false');
          break;
        case 'INACTIVE':
          whereClauses.push('(s.is_enabled = false OR s.last_synced IS NULL OR datetime() - s.last_synced > duration("P1D"))');
          break;
        case 'PAUSED':
          whereClauses.push('s.is_paused = true');
          break;
      }
    }

    if (whereClauses.length > 0) {
      query += ` WHERE ${whereClauses.join(' AND ')}`;
    }

    query += `
      RETURN s, fg.name AS groupName, fg.id AS groupId, e.id AS entityId, e.name AS entityName
      ORDER BY s.name
    `;

    const result = await session.run(query, params);

    return result.records.map((record) => {
      const source = record.get('s').properties;
      const groupName = record.get('groupName') || 'Uncategorized';
      const groupId = record.get('groupId');
      const entityId = record.get('entityId');
      const entityName = record.get('entityName');
      return mapSourceRecord(source, groupName, entityId, entityName, groupId);
    });
  } finally {
    await session.close();
  }
}

/**
 * Get a single source by ID
 */
export async function getSourceById(id: string): Promise<Source | null> {
  const session = getSession();
  try {
    const query = `
      MATCH (s:Source {id: $id})
      OPTIONAL MATCH (fg:FeedGroup)-[:CONTAINS]->(s)
      OPTIONAL MATCH (e:Entity)-[:HAS_SOURCE]->(s)
      RETURN s, fg.name AS groupName, fg.id AS groupId, e.id AS entityId, e.name AS entityName
    `;

    const result = await session.run(query, { id });

    if (result.records.length === 0) {
      return null;
    }

    const record = result.records[0];
    const source = record.get('s').properties;
    const groupName = record.get('groupName') || 'Uncategorized';
    const groupId = record.get('groupId');
    const entityId = record.get('entityId');
    const entityName = record.get('entityName');

    return mapSourceRecord(source, groupName, entityId, entityName, groupId);
  } finally {
    await session.close();
  }
}

/**
 * Create a new source
 */
export async function createSourceNode(input: CreateSourceInput): Promise<Source> {
  const session = getSession();
  try {
    const id = crypto.randomUUID();

    // First, ensure the feed group exists or use default
    let groupId = input.groupId;
    if (!groupId) {
      const groups = await getFeedGroups();
      groupId = groups[0]?.id;
    }

    const query = `
      MATCH (fg:FeedGroup {id: $groupId})
      CREATE (s:Source {
        id: $id,
        name: $name,
        source_type: $sourceType,
        subreddit_name: $subredditName,
        youtube_channel_handle: $youtubeHandle,
        twitter_handle: $twitterHandle,
        instagram_handle: $instagramHandle,
        tiktok_handle: $tiktokHandle,
        url: $url,
        rss_url: $url,
        description: $description,
        is_paused: false,
        is_enabled: true,
        media_count: 0,
        stories_per_month: 0,
        reads_per_month: 0,
        created_at: datetime()
      })
      CREATE (fg)-[:CONTAINS]->(s)
      RETURN s, fg.name AS groupName, fg.id AS groupId
    `;

    const result = await session.run(query, {
      id,
      groupId,
      name: input.name,
      sourceType: input.sourceType,
      subredditName: input.subredditName || null,
      youtubeHandle: input.youtubeHandle || null,
      twitterHandle: input.twitterHandle || null,
      instagramHandle: input.instagramHandle || null,
      tiktokHandle: input.tiktokHandle || null,
      url: input.url || null,
      description: input.description || null,
    });

    const record = result.records[0];
    const source = record.get('s').properties;
    const groupName = record.get('groupName');
    const resultGroupId = record.get('groupId');

    return mapSourceRecord(source, groupName, undefined, undefined, resultGroupId);
  } finally {
    await session.close();
  }
}

/**
 * Update an existing source
 */
export async function updateSourceNode(id: string, input: UpdateSourceInput): Promise<Source | null> {
  const session = getSession();
  try {
    const setClauses: string[] = ['s.updated_at = datetime()'];
    const params: Record<string, any> = { id };

    if (input.name !== undefined) {
      setClauses.push('s.name = $name');
      params.name = input.name;
    }
    if (input.description !== undefined) {
      setClauses.push('s.description = $description');
      params.description = input.description;
    }
    if (input.isPaused !== undefined) {
      setClauses.push('s.is_paused = $isPaused');
      params.isPaused = input.isPaused;
    }
    if (input.isEnabled !== undefined) {
      setClauses.push('s.is_enabled = $isEnabled');
      params.isEnabled = input.isEnabled;
    }

    let query = `
      MATCH (s:Source {id: $id})
      SET ${setClauses.join(', ')}
    `;

    // Handle group change
    if (input.groupId !== undefined) {
      query = `
        MATCH (s:Source {id: $id})
        OPTIONAL MATCH (oldFg:FeedGroup)-[oldRel:CONTAINS]->(s)
        DELETE oldRel
        WITH s
        MATCH (newFg:FeedGroup {id: $newGroupId})
        CREATE (newFg)-[:CONTAINS]->(s)
        SET ${setClauses.join(', ')}
      `;
      params.newGroupId = input.groupId;
    }

    query += `
      WITH s
      OPTIONAL MATCH (fg:FeedGroup)-[:CONTAINS]->(s)
      OPTIONAL MATCH (e:Entity)-[:HAS_SOURCE]->(s)
      RETURN s, fg.name AS groupName, fg.id AS groupId, e.id AS entityId, e.name AS entityName
    `;

    const result = await session.run(query, params);

    if (result.records.length === 0) {
      return null;
    }

    const record = result.records[0];
    const source = record.get('s').properties;
    const groupName = record.get('groupName') || 'Uncategorized';
    const groupId = record.get('groupId');
    const entityId = record.get('entityId');
    const entityName = record.get('entityName');

    return mapSourceRecord(source, groupName, entityId, entityName, groupId);
  } finally {
    await session.close();
  }
}

/**
 * Delete a source
 */
export async function deleteSourceNode(id: string): Promise<boolean> {
  const session = getSession();
  try {
    const query = `
      MATCH (s:Source {id: $id})
      DETACH DELETE s
      RETURN count(s) AS deleted
    `;

    const result = await session.run(query, { id });
    const deleted = result.records[0]?.get('deleted')?.toNumber() || 0;

    return deleted > 0;
  } finally {
    await session.close();
  }
}

/**
 * Bulk delete sources
 */
export async function bulkDeleteSources(ids: string[]): Promise<number> {
  const session = getSession();
  try {
    const query = `
      MATCH (s:Source)
      WHERE s.id IN $ids
      DETACH DELETE s
      RETURN count(s) AS deleted
    `;

    const result = await session.run(query, { ids });
    return result.records[0]?.get('deleted')?.toNumber() || 0;
  } finally {
    await session.close();
  }
}

/**
 * Toggle source pause state
 */
export async function toggleSourcePause(id: string): Promise<Source | null> {
  const session = getSession();
  try {
    const query = `
      MATCH (s:Source {id: $id})
      SET s.is_paused = NOT coalesce(s.is_paused, false),
          s.updated_at = datetime()
      WITH s
      OPTIONAL MATCH (fg:FeedGroup)-[:CONTAINS]->(s)
      OPTIONAL MATCH (e:Entity)-[:HAS_SOURCE]->(s)
      RETURN s, fg.name AS groupName, fg.id AS groupId, e.id AS entityId, e.name AS entityName
    `;

    const result = await session.run(query, { id });

    if (result.records.length === 0) {
      return null;
    }

    const record = result.records[0];
    const source = record.get('s').properties;
    const groupName = record.get('groupName') || 'Uncategorized';
    const groupId = record.get('groupId');
    const entityId = record.get('entityId');
    const entityName = record.get('entityName');

    return mapSourceRecord(source, groupName, entityId, entityName, groupId);
  } finally {
    await session.close();
  }
}

/**
 * Bulk create sources (for OPML import)
 */
export async function bulkCreateSources(
  sources: CreateSourceInput[],
  groupId?: string
): Promise<{ imported: number; skipped: number; failed: number; sources: Source[] }> {
  const session = getSession();
  try {
    // Ensure we have a group
    let targetGroupId = groupId;
    if (!targetGroupId) {
      const groups = await getFeedGroups();
      targetGroupId = groups[0]?.id;
    }

    const createdSources: Source[] = [];
    let imported = 0;
    let skipped = 0;
    let failed = 0;

    for (const input of sources) {
      try {
        // Check if source already exists (by URL or name)
        const checkQuery = `
          MATCH (s:Source)
          WHERE s.rss_url = $url OR (s.name = $name AND s.source_type = $sourceType)
          RETURN s
          LIMIT 1
        `;

        const checkResult = await session.run(checkQuery, {
          url: input.url || '',
          name: input.name,
          sourceType: input.sourceType,
        });

        if (checkResult.records.length > 0) {
          skipped++;
          continue;
        }

        // Create the source
        const id = crypto.randomUUID();
        const createQuery = `
          MATCH (fg:FeedGroup {id: $groupId})
          CREATE (s:Source {
            id: $id,
            name: $name,
            source_type: $sourceType,
            rss_url: $url,
            url: $url,
            description: $description,
            is_paused: false,
            is_enabled: true,
            media_count: 0,
            stories_per_month: 0,
            reads_per_month: 0,
            created_at: datetime()
          })
          CREATE (fg)-[:CONTAINS]->(s)
          RETURN s, fg.name AS groupName, fg.id AS groupId
        `;

        const createResult = await session.run(createQuery, {
          id,
          groupId: targetGroupId,
          name: input.name,
          sourceType: input.sourceType,
          url: input.url || null,
          description: input.description || null,
        });

        if (createResult.records.length > 0) {
          const record = createResult.records[0];
          const source = record.get('s').properties;
          const groupName = record.get('groupName');
          const resultGroupId = record.get('groupId');
          createdSources.push(mapSourceRecord(source, groupName, undefined, undefined, resultGroupId));
          imported++;
        }
      } catch {
        failed++;
      }
    }

    return {
      imported,
      skipped,
      failed,
      sources: createdSources,
    };
  } finally {
    await session.close();
  }
}
