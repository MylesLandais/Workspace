import { NextRequest, NextResponse } from 'next/server';

const GRAPHQL_ENDPOINT = process.env.GRAPHQL_API_URL || 'http://localhost:4002/api/graphql';

const FEED_QUERY = `
  query Feed($cursor: String, $limit: Int, $filters: FeedFilters) {
    feed(cursor: $cursor, limit: $limit, filters: $filters) {
      edges {
        node {
          id
          title
          imageUrl
          presignedUrl
          urlExpiresAt
          width
          height
          mediaType
          platform
          publishDate
          sha256
          mimeType
          storagePath
          handle {
            name
            handle
            creatorName
          }
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
`;

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const cursor = searchParams.get('cursor');
    const limit = parseInt(searchParams.get('limit') || '20');

    console.log(`[Feed API] Fetching feed: cursor=${cursor}, limit=${limit}`);
    console.log(`[Feed API] GraphQL endpoint: ${GRAPHQL_ENDPOINT}`);

    const response = await fetch(GRAPHQL_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: FEED_QUERY,
        variables: {
          cursor,
          limit,
          filters: {
            persons: [],
            sources: [],
            tags: [],
            searchQuery: '',
          },
        },
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Feed API] GraphQL HTTP error: ${response.status} ${response.statusText}`);
      console.error(`[Feed API] Response body: ${errorText}`);
      throw new Error(`GraphQL request failed: ${response.statusText}`);
    }

    const data = await response.json();

    if (data.errors) {
      console.error('[Feed API] GraphQL errors:', JSON.stringify(data.errors, null, 2));
      return NextResponse.json(
        { error: 'Failed to fetch feed data', details: data.errors },
        { status: 500 }
      );
    }

    if (!data.data || !data.data.feed) {
      console.error('[Feed API] Invalid GraphQL response structure:', JSON.stringify(data, null, 2));
      return NextResponse.json(
        { error: 'Invalid response from GraphQL server' },
        { status: 500 }
      );
    }

    console.log(`[Feed API] Successfully fetched ${data.data.feed.edges.length} items`);
    return NextResponse.json(data.data.feed);
  } catch (error) {
    console.error('[Feed API] CRITICAL ERROR:', error);
    if (error instanceof Error) {
      console.error('[Feed API] Error stack:', error.stack);
    }
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
