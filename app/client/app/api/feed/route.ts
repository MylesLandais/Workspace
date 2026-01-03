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
    const searchQuery = searchParams.get('searchQuery') || '';
    const persons = searchParams.get('persons')?.split(',').filter(Boolean) || [];
    const sources = searchParams.get('sources')?.split(',').filter(Boolean) || [];
    const tags = searchParams.get('tags')?.split(',').filter(Boolean) || [];
    const categories = searchParams.get('categories')?.split(',').filter(Boolean) || [];

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
            persons,
            sources,
            tags,
            searchQuery,
            categories,
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
      return NextResponse.json(
        { error: 'Failed to fetch feed data', details: data.errors },
        { status: 500 }
      );
    }

    if (!data.data || !data.data.feed) {
      return NextResponse.json(
        { error: 'Invalid response from GraphQL server' },
        { status: 500 }
      );
    }

    return NextResponse.json(data.data.feed);
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
