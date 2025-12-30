import { getSession } from '../driver.js';

export interface Creator {
  id: string;
  slug: string;
  name: string;
  displayName: string;
  bio?: string;
  avatarUrl?: string;
  verified: boolean;
  handles: Handle[];
}

export interface Handle {
  id: string;
  platform: string;
  username: string;
  handle: string;
  url: string;
  verified: boolean;
  status: string;
  mediaCount: number;
  lastSynced: string | null;
  health: string;
}

export async function getCreators(query?: string, limit: number = 20): Promise<Creator[]> {
  const session = getSession();
  try {
    let cypher = `
      MATCH (e:Entity)
    `;

    const params: any = { limit };

    if (query) {
      cypher += ` WHERE e.name CONTAINS $query OR e.id CONTAINS $query`;
      params.query = query;
    }

    cypher += `
      OPTIONAL MATCH (e)-[:HAS_SOURCE]->(s:Source)
      WITH e, collect(s) AS sources
      RETURN e, sources
      ORDER BY e.name
      LIMIT $limit
    `;

    const result = await session.run(cypher, params);

    return result.records.map((record) => {
      const entity = record.get('e').properties;
      const sources = record.get('sources') || [];

      const handles: Handle[] = sources.map((source: any) => {
        const props = source.properties;
        const lastSynced = props.last_synced ? new Date(props.last_synced.toString()).toISOString() : null;
        
        let health = 'red';
        if (lastSynced) {
          const hoursAgo = (Date.now() - new Date(lastSynced).getTime()) / (1000 * 60 * 60);
          if (hoursAgo < 1) health = 'green';
          else if (hoursAgo < 24) health = 'yellow';
        }

        const platform = props.source_type || 'reddit';
        let handleStr = '';
        if (platform === 'reddit') {
          handleStr = `r/${props.subreddit_name || props.name}`;
        } else if (platform === 'youtube') {
          handleStr = props.youtube_channel_handle || `@${props.name}`;
        } else {
          handleStr = props.name;
        }

        return {
          id: props.id,
          platform,
          username: props.subreddit_name || props.youtube_channel_handle || props.name,
          handle: handleStr,
          url: props.url || '',
          verified: props.verified || false,
          status: props.status || 'active',
          mediaCount: props.media_count || 0,
          lastSynced,
          health,
        };
      });

      return {
        id: entity.id,
        slug: entity.id,
        name: entity.name || '',
        displayName: entity.name || '',
        bio: entity.description,
        avatarUrl: entity.avatar_url,
        verified: entity.verified || false,
        handles,
      };
    });
  } finally {
    await session.close();
  }
}

export async function getCreatorBySlug(slug: string): Promise<Creator | null> {
  const session = getSession();
  try {
    const query = `
      MATCH (e:Entity {id: $slug})
      OPTIONAL MATCH (e)-[:HAS_SOURCE]->(s:Source)
      RETURN e, collect(s) AS sources
    `;

    const result = await session.run(query, { slug });

    if (result.records.length === 0) {
      return null;
    }

    const record = result.records[0];
    const entity = record.get('e').properties;
    const sources = record.get('sources') || [];

    const handles: Handle[] = sources.map((source: any) => {
      const props = source.properties;
      const lastSynced = props.last_synced ? new Date(props.last_synced.toString()).toISOString() : null;
      
      let health = 'red';
      if (lastSynced) {
        const hoursAgo = (Date.now() - new Date(lastSynced).getTime()) / (1000 * 60 * 60);
        if (hoursAgo < 1) health = 'green';
        else if (hoursAgo < 24) health = 'yellow';
      }

      const platform = props.source_type || 'reddit';
      let handleStr = '';
      if (platform === 'reddit') {
        handleStr = `r/${props.subreddit_name || props.name}`;
      } else if (platform === 'youtube') {
        handleStr = props.youtube_channel_handle || `@${props.name}`;
      } else {
        handleStr = props.name;
      }

      return {
        id: props.id,
        platform,
        username: props.subreddit_name || props.youtube_channel_handle || props.name,
        handle: handleStr,
        url: props.url || '',
        verified: props.verified || false,
        status: props.status || 'active',
        mediaCount: props.media_count || 0,
        lastSynced,
        health,
      };
    });

    return {
      id: entity.id,
      slug: entity.id,
      name: entity.name || '',
      displayName: entity.name || '',
      bio: entity.description,
      avatarUrl: entity.avatar_url,
      verified: entity.verified || false,
      handles,
    };
  } finally {
    await session.close();
  }
}


