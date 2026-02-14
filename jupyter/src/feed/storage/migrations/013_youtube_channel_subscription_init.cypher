// Init script: Load test YouTube creators and channels into Neo4j
// This script sets up Fasffy and Miss Katie as test creators with YouTube handles

// ============================================================================
// YOUTUBE CHANNEL SUBSCRIPTION INIT SCRIPT
// ============================================================================

// Clear existing test data (optional - comment out to preserve data)
// MATCH (c:Creator) WHERE c.slug IN ['fasffy', 'misskatie'] DETACH DELETE c

// ============================================================================
// CREATE YOUTUBE PLATFORM
// ============================================================================

MERGE (p:Platform {slug: 'youtube'})
SET p.name = 'YouTube',
    p.api_base_url = 'https://www.googleapis.com/youtube/v3',
    p.icon_url = 'https://www.youtube.com/favicon.ico',
    p.created_at = COALESCE(p.created_at, datetime()),
    p.updated_at = datetime()
RETURN p as youtube_platform

// ============================================================================
// CREATE FASFFY CREATOR
// ============================================================================

MERGE (c1:Creator {slug: 'fasffy'})
SET c1.name = 'Fasffy',
    c1.bio = 'Content creator and streamer - Testing memes and challenges',
    c1.avatar_url = 'https://example.com/fasffy-avatar.jpg',
    c1.uuid = COALESCE(c1.uuid, '550e8400-e29b-41d4-a716-446655440001'),
    c1.created_at = COALESCE(c1.created_at, datetime()),
    c1.updated_at = datetime()
RETURN c1 as fasffy_creator

// ============================================================================
// CREATE FASFFY YOUTUBE HANDLE
// ============================================================================

MATCH (c1:Creator {slug: 'fasffy'})
MATCH (p:Platform {slug: 'youtube'})
MERGE (h1:Handle {profile_url: 'https://www.youtube.com/@Fasffy'})
SET h1.uuid = COALESCE(h1.uuid, '660e8400-e29b-41d4-a716-446655440001'),
    h1.username = '@Fasffy',
    h1.display_name = 'Fasffy',
    h1.follower_count = 150000,
    h1.verified_by_platform = true,
    h1.created_at = COALESCE(h1.created_at, datetime()),
    h1.updated_at = datetime()
MERGE (c1)-[r1:OWNS_HANDLE]->(h1)
SET r1.status = 'Active',
    r1.verified = true,
    r1.confidence = 'High',
    r1.discovered_at = COALESCE(r1.discovered_at, datetime()),
    r1.created_at = COALESCE(r1.created_at, datetime()),
    r1.updated_at = datetime()
MERGE (h1)-[:ON_PLATFORM]->(p)
RETURN h1 as fasffy_handle, r1 as fasffy_relationship

// ============================================================================
// CREATE FASFFY SUBSCRIPTION TO YOUTUBE
// ============================================================================

MATCH (c1:Creator {slug: 'fasffy'})
MATCH (p:Platform {slug: 'youtube'})
MERGE (c1)-[sub1:SUBSCRIBED_TO]->(p)
SET sub1.status = 'active',
    sub1.poll_interval_hours = 1,
    sub1.last_polled_at = datetime() - duration('PT2H'),
    sub1.last_successful_poll = datetime() - duration('PT2H'),
    sub1.poll_count_24h = 24,
    sub1.error_count_24h = 0,
    sub1.created_at = COALESCE(sub1.created_at, datetime()),
    sub1.updated_at = datetime()
RETURN sub1 as fasffy_subscription

// ============================================================================
// CREATE MISS KATIE CREATOR
// ============================================================================

MERGE (c2:Creator {slug: 'misskatie'})
SET c2.name = 'Miss Katie',
    c2.bio = 'YouTube content creator - Lifestyle and vlogs',
    c2.avatar_url = 'https://example.com/misskatie-avatar.jpg',
    c2.uuid = COALESCE(c2.uuid, '550e8400-e29b-41d4-a716-446655440002'),
    c2.created_at = COALESCE(c2.created_at, datetime()),
    c2.updated_at = datetime()
RETURN c2 as misskatie_creator

// ============================================================================
// CREATE MISS KATIE YOUTUBE HANDLE
// ============================================================================

MATCH (c2:Creator {slug: 'misskatie'})
MATCH (p:Platform {slug: 'youtube'})
MERGE (h2:Handle {profile_url: 'https://www.youtube.com/@MissKatie'})
SET h2.uuid = COALESCE(h2.uuid, '660e8400-e29b-41d4-a716-446655440002'),
    h2.username = '@MissKatie',
    h2.display_name = 'Miss Katie',
    h2.follower_count = 85000,
    h2.verified_by_platform = true,
    h2.created_at = COALESCE(h2.created_at, datetime()),
    h2.updated_at = datetime()
MERGE (c2)-[r2:OWNS_HANDLE]->(h2)
SET r2.status = 'Active',
    r2.verified = true,
    r2.confidence = 'High',
    r2.discovered_at = COALESCE(r2.discovered_at, datetime()),
    r2.created_at = COALESCE(r2.created_at, datetime()),
    r2.updated_at = datetime()
MERGE (h2)-[:ON_PLATFORM]->(p)
RETURN h2 as misskatie_handle, r2 as misskatie_relationship

// ============================================================================
// CREATE MISS KATIE SUBSCRIPTION TO YOUTUBE
// ============================================================================

MATCH (c2:Creator {slug: 'misskatie'})
MATCH (p:Platform {slug: 'youtube'})
MERGE (c2)-[sub2:SUBSCRIBED_TO]->(p)
SET sub2.status = 'active',
    sub2.poll_interval_hours = 1,
    sub2.last_polled_at = datetime() - duration('PT1H'),
    sub2.last_successful_poll = datetime() - duration('PT1H'),
    sub2.poll_count_24h = 48,
    sub2.error_count_24h = 1,
    sub2.created_at = COALESCE(sub2.created_at, datetime()),
    sub2.updated_at = datetime()
RETURN sub2 as misskatie_subscription

// ============================================================================
// CREATE SAMPLE MEDIA (VIDEOS) FOR FASFFY
// ============================================================================

MATCH (c1:Creator {slug: 'fasffy'})
MATCH (p:Platform {slug: 'youtube'})
MERGE (v1:Media:Video {source_url: 'https://www.youtube.com/watch?v=2vh31BrqhJQ'})
SET v1.uuid = '770e8400-e29b-41d4-a716-446655440001',
    v1.title = 'These Memes Challenge Me...',
    v1.media_type = 'Video',
    v1.publish_date = datetime() - duration('P3D'),
    v1.thumbnail_url = 'https://i.ytimg.com/vi/2vh31BrqhJQ/maxresdefault.jpg',
    v1.duration = 624,
    v1.view_count = 125000,
    v1.aspect_ratio = '16:9',
    v1.resolution = '1080p',
    v1.created_at = datetime(),
    v1.updated_at = datetime()

MATCH (h1:Handle {profile_url: 'https://www.youtube.com/@Fasffy'})
MERGE (h1)-[pub1:PUBLISHED]->(v1)
SET pub1.published_at = datetime() - duration('P3D'),
    pub1.engagement_score = 0.85

MERGE (v1)-[:SOURCED_FROM]->(p)
RETURN v1 as fasffy_video1

// ============================================================================
// CREATE SAMPLE MEDIA (VIDEOS) FOR MISS KATIE
// ============================================================================

MATCH (c2:Creator {slug: 'misskatie'})
MATCH (p:Platform {slug: 'youtube'})
MERGE (v2:Media:Video {source_url: 'https://www.youtube.com/watch?v=dummy123'})
SET v2.uuid = '770e8400-e29b-41d4-a716-446655440002',
    v2.title = 'A Day in My Life',
    v2.media_type = 'Video',
    v2.publish_date = datetime() - duration('P1D'),
    v2.thumbnail_url = 'https://i.ytimg.com/vi/dummy123/maxresdefault.jpg',
    v2.duration = 845,
    v2.view_count = 45000,
    v2.aspect_ratio = '9:16',
    v2.resolution = '1080p',
    v2.created_at = datetime(),
    v2.updated_at = datetime()

MATCH (h2:Handle {profile_url: 'https://www.youtube.com/@MissKatie'})
MERGE (h2)-[pub2:PUBLISHED]->(v2)
SET pub2.published_at = datetime() - duration('P1D'),
    pub2.engagement_score = 0.72

MERGE (v2)-[:SOURCED_FROM]->(p)
RETURN v2 as misskatie_video1

// ============================================================================
// VERIFY SETUP
// ============================================================================

MATCH (c:Creator)
WHERE c.slug IN ['fasffy', 'misskatie']
OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)
OPTIONAL MATCH (c)-[sub:SUBSCRIBED_TO]->(p:Platform {slug: 'youtube'})
OPTIONAL MATCH (h)-[pub:PUBLISHED]->(v:Media:Video)
RETURN 
    c.slug as creator_slug,
    c.name as creator_name,
    h.username as youtube_handle,
    h.profile_url as youtube_url,
    sub.status as subscription_status,
    sub.last_polled_at as last_polled,
    count(v) as video_count
ORDER BY c.name
