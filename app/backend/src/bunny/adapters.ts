import { Creator, Handle } from '../neo4j/queries/creators.js';
import { IdentityProfile, SourceLink, Relationship } from '../../../../frontend/src/lib/bunny/types';

/**
 * Converts a Creator + Handles to an IdentityProfile
 */
export function creatorToIdentityProfile(creator: Creator, handles: Handle[]): IdentityProfile {
  const sources: SourceLink[] = handles.map(handle => ({
    platform: handle.platform.toLowerCase() as SourceLink['platform'],
    id: handle.username,
    label: handle.label || undefined,
    hidden: handle.hidden || false,
  }));

  return {
    id: creator.id,
    name: creator.name,
    bio: creator.bio || '',
    avatarUrl: creator.avatarUrl || '',
    aliases: creator.aliases || [],
    sources,
    contextKeywords: creator.contextKeywords || [],
    imagePool: creator.imagePool || [],
    relationships: creator.relationships || [],
  };
}

/**
 * Converts an IdentityProfile to Creator data for Neo4j
 */
export function identityProfileToCreatorData(profile: IdentityProfile) {
  return {
    id: profile.id,
    name: profile.name,
    displayName: profile.name,
    bio: profile.bio,
    avatarUrl: profile.avatarUrl,
    aliases: profile.aliases,
    contextKeywords: profile.contextKeywords,
    imagePool: profile.imagePool,
  };
}

/**
 * Converts SourceLink to Handle data for Neo4j
 */
export function sourceLinkToHandleData(sourceLink: SourceLink, creatorId: string) {
  return {
    platform: sourceLink.platform.toUpperCase(),
    username: sourceLink.id,
    handle: sourceLink.id,
    url: `https://${sourceLink.platform}.com/${sourceLink.id}`,
    label: sourceLink.label || null,
    hidden: sourceLink.hidden || false,
    creatorId,
  };
}





