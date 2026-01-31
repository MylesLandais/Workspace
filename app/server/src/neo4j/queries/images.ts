import { getSession } from "../driver.js";
import { v4 as uuidv4 } from "uuid";

export interface ImageCluster {
  id: string;
  canonicalSha256: string;
  firstSeen: string;
  lastSeen: string;
  repostCount: number;
}

export interface MediaWithHashes {
  id: string;
  sha256: string;
  phash: string;
  dhash: string;
  width: number;
  height: number;
  sizeBytes: number;
  mimeType: string;
  url: string;
  storagePath: string;
  createdAt: string;
  clusterId?: string;
}

export async function createImageCluster(
  canonicalSha256: string,
  firstSeen: Date,
): Promise<string> {
  const session = getSession();
  try {
    const clusterId = uuidv4();
    const query = `
      CREATE (c:ImageCluster {
        id: $clusterId,
        canonical_sha256: $canonicalSha256,
        first_seen: datetime($firstSeen),
        last_seen: datetime($firstSeen),
        repost_count: 1
      })
      RETURN c.id AS id
    `;

    const result = await session.run(query, {
      clusterId,
      canonicalSha256,
      firstSeen: firstSeen.toISOString(),
    });

    return result.records[0].get("id");
  } finally {
    await session.close();
  }
}

export async function createMediaWithHashes(mediaData: {
  sha256: string;
  phash: bigint;
  dhash: bigint;
  width: number;
  height: number;
  sizeBytes: number;
  mimeType: string;
  url: string;
  storagePath: string;
  createdAt: Date;
}): Promise<string> {
  const session = getSession();
  try {
    const mediaId = uuidv4();
    const query = `
      CREATE (m:Media {
        id: $mediaId,
        sha256: $sha256,
        phash: $phash,
        dhash: $dhash,
        width: $width,
        height: $height,
        size_bytes: $sizeBytes,
        mime_type: $mimeType,
        url: $url,
        storage_path: $storagePath,
        created_at: datetime($createdAt),
        ingested_at: datetime()
      })
      RETURN m.id AS id
    `;

    const result = await session.run(query, {
      mediaId,
      sha256: mediaData.sha256,
      phash: mediaData.phash.toString(),
      dhash: mediaData.dhash.toString(),
      width: mediaData.width,
      height: mediaData.height,
      sizeBytes: mediaData.sizeBytes,
      mimeType: mediaData.mimeType,
      url: mediaData.url,
      storagePath: mediaData.storagePath,
      createdAt: mediaData.createdAt.toISOString(),
    });

    return result.records[0].get("id");
  } finally {
    await session.close();
  }
}

export async function linkMediaToCluster(
  mediaId: string,
  clusterId: string,
  confidence: number,
): Promise<void> {
  const session = getSession();
  try {
    const query = `
      MATCH (m:Media {id: $mediaId})
      MATCH (c:ImageCluster {id: $clusterId})
      MERGE (m)-[r:BELONGS_TO]->(c)
      SET r.confidence = $confidence,
          r.assigned_at = datetime()
    `;

    await session.run(query, { mediaId, clusterId, confidence });
  } finally {
    await session.close();
  }
}

export async function setCanonicalImage(
  clusterId: string,
  mediaId: string,
): Promise<void> {
  const session = getSession();
  try {
    const query = `
      MATCH (c:ImageCluster {id: $clusterId})
      MATCH (m:Media {id: $mediaId})
      MERGE (c)-[r:CANONICAL]->(m)
    `;

    await session.run(query, { clusterId, mediaId });
  } finally {
    await session.close();
  }
}

export async function updateClusterLastSeen(
  clusterId: string,
  lastSeen: Date,
): Promise<void> {
  const session = getSession();
  try {
    const query = `
      MATCH (c:ImageCluster {id: $clusterId})
      SET c.last_seen = datetime($lastSeen)
    `;

    await session.run(query, { clusterId, lastSeen: lastSeen.toISOString() });
  } finally {
    await session.close();
  }
}

export async function incrementClusterRepostCount(
  clusterId: string,
): Promise<void> {
  const session = getSession();
  try {
    const query = `
      MATCH (c:ImageCluster {id: $clusterId})
      SET c.repost_count = c.repost_count + 1
    `;

    await session.run(query, { clusterId });
  } finally {
    await session.close();
  }
}

export async function createRepostRelationship(
  repostMediaId: string,
  originalMediaId: string,
  confidence: number,
  method: string,
): Promise<void> {
  const session = getSession();
  try {
    const query = `
      MATCH (repost:Media {id: $repostMediaId})
      MATCH (original:Media {id: $originalMediaId})
      MERGE (repost)-[r:REPOST_OF]->(original)
      SET r.confidence = $confidence,
          r.detected_method = $method,
          r.detected_at = datetime()
    `;

    await session.run(query, {
      repostMediaId,
      originalMediaId,
      confidence,
      method,
    });
  } finally {
    await session.close();
  }
}

export async function linkMediaToPost(
  mediaId: string,
  postId: string,
  position: number = 0,
): Promise<void> {
  const session = getSession();
  try {
    const query = `
      MATCH (m:Media {id: $mediaId})
      MATCH (p:Post {id: $postId})
      MERGE (m)-[r:APPEARED_IN]->(p)
      SET r.position = $position
    `;

    await session.run(query, { mediaId, postId, position });
  } finally {
    await session.close();
  }
}

export async function getClusterById(
  clusterId: string,
): Promise<ImageCluster | null> {
  const session = getSession();
  try {
    const query = `
      MATCH (c:ImageCluster {id: $clusterId})
      OPTIONAL MATCH (c)-[:CANONICAL]->(canonical:Media)
      RETURN c.id AS id,
             c.canonical_sha256 AS canonicalSha256,
             c.first_seen AS firstSeen,
             c.last_seen AS lastSeen,
             c.repost_count AS repostCount,
             canonical.id AS canonicalMediaId,
             canonical.sha256 AS canonicalSha256FromMedia
    `;

    const result = await session.run(query, { clusterId });
    if (result.records.length === 0) {
      return null;
    }

    const record = result.records[0];
    return {
      id: record.get("id"),
      canonicalSha256:
        record.get("canonicalSha256") || record.get("canonicalSha256FromMedia"),
      firstSeen:
        record.get("firstSeen")?.toString() || new Date().toISOString(),
      lastSeen: record.get("lastSeen")?.toString() || new Date().toISOString(),
      repostCount: record.get("repostCount")?.toNumber() || 0,
    };
  } finally {
    await session.close();
  }
}

export async function getMediaById(
  mediaId: string,
): Promise<MediaWithHashes | null> {
  const session = getSession();
  try {
    const query = `
      MATCH (m:Media {id: $mediaId})
      OPTIONAL MATCH (m)-[:BELONGS_TO]->(c:ImageCluster)
      RETURN m.id AS id,
             m.sha256 AS sha256,
             m.phash AS phash,
             m.dhash AS dhash,
             m.width AS width,
             m.height AS height,
             m.size_bytes AS sizeBytes,
             m.mime_type AS mimeType,
             m.url AS url,
             m.storage_path AS storagePath,
             m.created_at AS createdAt,
             c.id AS clusterId
    `;

    const result = await session.run(query, { mediaId });
    if (result.records.length === 0) {
      return null;
    }

    const record = result.records[0];
    return {
      id: record.get("id"),
      sha256: record.get("sha256"),
      phash: record.get("phash"),
      dhash: record.get("dhash"),
      width: record.get("width").toNumber(),
      height: record.get("height").toNumber(),
      sizeBytes: record.get("sizeBytes").toNumber(),
      mimeType: record.get("mimeType"),
      url: record.get("url"),
      storagePath: record.get("storagePath"),
      createdAt: record.get("createdAt").toString(),
      clusterId: record.get("clusterId"),
    };
  } finally {
    await session.close();
  }
}

export async function getImageLineage(mediaId: string): Promise<{
  original: MediaWithHashes | null;
  reposts: Array<{
    media: MediaWithHashes;
    postId: string;
    createdAt: string;
    confidence: number;
  }>;
}> {
  const session = getSession();
  try {
    const query = `
      MATCH (m:Media {id: $mediaId})-[:BELONGS_TO]->(c:ImageCluster)
      MATCH (all:Media)-[:BELONGS_TO]->(c)
      OPTIONAL MATCH (all)-[:APPEARED_IN]->(p:Post)
      WITH all, c, p, all.created_at AS created
      ORDER BY created ASC
      WITH collect({mediaId: all.id, postId: p.id, created: created}) AS members
      
      MATCH (original:Media)-[:BELONGS_TO]->(c)
      OPTIONAL MATCH (original)-[:APPEARED_IN]->(origPost:Post)
      WITH members, original.id AS originalId, origPost.id AS originalPostId, original.created_at AS origCreated
      ORDER BY origCreated ASC
      LIMIT 1
      
      RETURN originalId, originalPostId, members AS allMembers
    `;

    const result = await session.run(query, { mediaId });
    if (result.records.length === 0) {
      return { original: null, reposts: [] };
    }

    const record = result.records[0];
    const originalId = record.get("originalId");
    const original = originalId ? await getMediaById(originalId) : null;

    const members = record.get("allMembers") || [];
    const reposts = [];

    for (const member of members) {
      if (member.mediaId !== originalId) {
        const media = await getMediaById(member.mediaId);
        if (media) {
          reposts.push({
            media,
            postId: member.postId || "",
            createdAt: member.created?.toString() || "",
            confidence: 0.95,
          });
        }
      }
    }

    return { original, reposts };
  } finally {
    await session.close();
  }
}

export async function getSimilarImages(
  mediaId: string,
  limit: number = 10,
): Promise<
  Array<{
    media: MediaWithHashes;
    similarity: number;
    method: string;
  }>
> {
  const session = getSession();
  try {
    const query = `
      MATCH (m:Media {id: $mediaId})-[:BELONGS_TO]->(c:ImageCluster)
      MATCH (similar:Media)-[:BELONGS_TO]->(c)
      WHERE similar.id <> $mediaId
      RETURN similar.id AS similarId
      LIMIT $limit
    `;

    const result = await session.run(query, { mediaId, limit });
    const similar = [];

    for (const record of result.records) {
      const similarId = record.get("similarId");
      const media = await getMediaById(similarId);
      if (media) {
        similar.push({
          media,
          similarity: 0.95,
          method: "cluster",
        });
      }
    }

    return similar;
  } finally {
    await session.close();
  }
}
