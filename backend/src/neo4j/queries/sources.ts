import { getSession } from '../driver.js';

export interface Source {
  id: string;
  name: string;
  subredditName?: string;
  sourceType: string;
  youtubeHandle?: string;
  entityId?: string;
  entityName?: string;
  group: string;
  tags: string[];
  isPaused: boolean;
  lastSynced: string | null;
  mediaCount: number;
  health: string;
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

      const lastSynced = source.last_synced ? new Date(source.last_synced.toString()).toISOString() : null;
      
      let health = 'red';
      if (lastSynced) {
        const hoursAgo = (Date.now() - new Date(lastSynced).getTime()) / (1000 * 60 * 60);
        if (hoursAgo < 1) health = 'green';
        else if (hoursAgo < 24) health = 'yellow';
      }

      return {
        id: source.id,
        name: source.name,
        subredditName: source.subreddit_name,
        sourceType: source.source_type || 'reddit',
        youtubeHandle: source.youtube_channel_handle,
        entityId: entityId || undefined,
        entityName: entityName || undefined,
        group: groupName,
        tags: [],
        isPaused: source.is_paused || false,
        lastSynced,
        mediaCount: source.media_count || 0,
        health,
      };
    });
  } finally {
    await session.close();
  }
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


