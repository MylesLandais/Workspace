#!/usr/bin/env node
/**
 * Generate GraphQL-formatted mock data from raw Reddit JSON
 * 
 * This script:
 * 1. Reads raw Reddit posts from /temp/mock_data/
 * 2. Transforms them into GraphQL schema format
 * 3. Outputs pre-transformed JSON files that match what the GraphQL API would return
 * 
 * Usage:
 *   npm run generate-graphql-mock-data
 *   npm run generate-graphql-mock-data -- --size=small
 *   npm run generate-graphql-mock-data -- --size=large
 */

import * as fs from 'fs/promises';
import * as path from 'path';

interface RawRedditPost {
  id: string;
  title: string;
  score: number;
  created_utc: string;
  image_url?: string;
  is_image?: boolean;
  author?: string;
  subreddit: string;
}

interface GraphQLFeedNode {
  id: string;
  title: string;
  imageUrl: string | null;
  sourceUrl: string;
  publishDate: string; // ISO 8601
  score: number;
  width: number | null;
  height: number | null;
  subreddit: {
    name: string;
  };
  author: {
    username: string;
  };
  platform: 'REDDIT';
  handle: {
    name: string;
    handle: string;
  };
  mediaType: 'IMAGE' | 'VIDEO' | 'TEXT';
  viewCount: number;
}

interface GraphQLFeedEdge {
  node: GraphQLFeedNode;
  cursor: string; // ISO 8601 timestamp
}

interface GraphQLFeedConnection {
  edges: GraphQLFeedEdge[];
  pageInfo: {
    hasNextPage: boolean;
    endCursor: string | null;
  };
}

// Priority subreddits for smaller datasets
const PRIORITY_SUBREDDITS = [
  'SelenaGomez',
  'TaylorSwift',
  'TaylorSwiftCandids',
  'TaylorSwiftMidriff',
  'Taylorhillfantasy',
  'ArianaGrande',
  'Pokimane',
  'SydneySweeney',
  'AddisonRae',
];

// All subreddits (from loader.ts)
const ALL_SUBREDDITS = [
  'AddisonRae', 'angourierice', 'annakendrick', 'ArianaGrande', 'BestOfBrookeMonk',
  'BotezLive', 'BrookeMonkTheSecond', 'BrookeMonkNSFWHub', 'HannahBeast',
  'KatrinaBowden', 'KiraKosarin', 'KiraKosarinLewd', 'LeightonMeester',
  'MargotRobbie', 'MarinKitagawaR34', 'McKaylaMaroney', 'MelissaBenoist',
  'MinkaKelly', 'MirandaKerr', 'NatalieDormer', 'NinaDobrev', 'Nina_Agdal',
  'OliviaRodrigoNSFW', 'OneTrueMentalOut', 'OvileeWorship', 'PhoebeTonkin',
  'Pokimane', 'PortiaDoubleday', 'RachelCook', 'RachelMcAdams', 'SammiHanratty',
  'SaraSampaio', 'SarahHyland', 'SelenaGomez', 'ShaileneWoodley', 'SommerRay',
  'StellaMaxwell', 'SydneySweeney', 'TOS_girls', 'TaylorSwiftCandids',
  'TaylorSwiftMidriff', 'Taylorhillfantasy', 'VanessaHudgens', 'VolleyballGirls',
  'WatchItForThePlot', 'WhatAWeeb', 'blakelively', 'candiceswanepoel',
  'erinmoriartyNEW', 'haydenpanettiere', 'howdyhowdyyallhot', 'islafisher',
  'jenniferlovehewitt', 'jessicaalba', 'karliekloss', 'kateupton',
  'kayascodelario', 'kendalljenner', 'kristenbell', 'kristinefroseth',
  'lizgillies', 'milanavayntrub', 'natalieportman', 'oliviadunne',
  'popheadscirclejerk', 'sophieturner', 'sunisalee', 'TaylorSwift',
  'victoriajustice', 'victorious', 'vsangels'
];

function transformPostToGraphQL(
  post: RawRedditPost,
  subredditName: string
): GraphQLFeedNode | null {
  // Only include image posts with valid image URLs
  if (!post.is_image || !post.image_url) {
    return null;
  }

  // Extract author username (handle Reddit's u/ prefix)
  const authorName = post.author
    ? post.author.replace('/u/', '').replace('u/', '').trim() || 'Unknown'
    : 'Unknown';

  // Parse timestamp
  const publishDate = new Date(post.created_utc * 1000).toISOString();

  return {
    id: post.id,
    title: post.title,
    imageUrl: post.image_url,
    sourceUrl: `https://reddit.com/r/${subredditName}/comments/${post.id}`,
    publishDate,
    score: post.score || 0,
    width: null, // Could extract from image metadata if available
    height: null,
    subreddit: {
      name: subredditName,
    },
    author: {
      username: authorName,
    },
    platform: 'REDDIT',
    handle: {
      name: `r/${subredditName}`,
      handle: `r/${subredditName}`,
    },
    mediaType: 'IMAGE',
    viewCount: 0,
  };
}

async function loadSubredditData(
  subredditName: string,
  mockDataDir: string
): Promise<GraphQLFeedNode[]> {
  const jsonPath = path.join(
    mockDataDir,
    subredditName,
    'json',
    `${subredditName}_posts.json`
  );

  try {
    const fileContent = await fs.readFile(jsonPath, 'utf-8');
    const data = JSON.parse(fileContent);
    const posts: RawRedditPost[] = data.posts || [];

    const transformed = posts
      .map((post) => transformPostToGraphQL(post, subredditName))
      .filter((node): node is GraphQLFeedNode => node !== null);

    return transformed;
  } catch (error) {
    console.warn(`Failed to load ${subredditName}:`, error);
    return [];
  }
}

async function generateGraphQLMockData(
  size: 'small' | 'medium' | 'large' = 'medium'
) {
  // Support running from both root and app/frontend directories
  const rootDir = process.cwd().endsWith('frontend') 
    ? path.join(process.cwd(), '../..')
    : process.cwd();
  const mockDataDir = path.join(rootDir, 'temp/mock_data');
  const outputDir = path.join(process.cwd(), 'public/temp/graphql-mock-data');

  // Ensure output directory exists
  await fs.mkdir(outputDir, { recursive: true });

  // Select subreddits based on size
  const subreddits =
    size === 'small'
      ? PRIORITY_SUBREDDITS
      : size === 'large'
      ? ALL_SUBREDDITS
      : [...PRIORITY_SUBREDDITS, ...ALL_SUBREDDITS.slice(0, 20)]; // medium: priority + 20 more

  console.log(`Generating ${size} dataset with ${subreddits.length} subreddits...`);

  const allNodes: GraphQLFeedNode[] = [];

  // Load and transform all subreddits
  for (const subreddit of subreddits) {
    console.log(`Loading ${subreddit}...`);
    const nodes = await loadSubredditData(subreddit, mockDataDir);
    allNodes.push(...nodes);
    console.log(`  ✓ Loaded ${nodes.length} posts`);
  }

  // Sort by publish date (newest first)
  allNodes.sort((a, b) => {
    return new Date(b.publishDate).getTime() - new Date(a.publishDate).getTime();
  });

  // Remove duplicates by ID
  const seen = new Set<string>();
  const uniqueNodes = allNodes.filter((node) => {
    if (seen.has(node.id)) {
      return false;
    }
    seen.add(node.id);
    return true;
  });

  console.log(`\nTotal unique posts: ${uniqueNodes.length}`);

  // Create FeedConnection structure
  const feedConnection: GraphQLFeedConnection = {
    edges: uniqueNodes.map((node) => ({
      node,
      cursor: node.publishDate,
    })),
    pageInfo: {
      hasNextPage: false, // Could calculate based on limit if needed
      endCursor: uniqueNodes.length > 0 ? uniqueNodes[uniqueNodes.length - 1].publishDate : null,
    },
  };

  // Write output files
  const outputPath = path.join(outputDir, `feed-${size}.json`);
  await fs.writeFile(outputPath, JSON.stringify(feedConnection, null, 2));

  // Also write a metadata file
  const metadata = {
    generatedAt: new Date().toISOString(),
    size,
    subredditCount: subreddits.length,
    postCount: uniqueNodes.length,
    subreddits,
  };
  const metadataPath = path.join(outputDir, `feed-${size}-metadata.json`);
  await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2));

  console.log(`\n✓ Generated: ${outputPath}`);
  console.log(`✓ Metadata: ${metadataPath}`);
  console.log(`\nUsage in MSW handlers:`);
  console.log(`  import feedData from '/temp/graphql-mock-data/feed-${size}.json';`);
}

// Main
const sizeArg = process.argv.find((arg) => arg.startsWith('--size='));
const size = (sizeArg?.split('=')[1] as 'small' | 'medium' | 'large') || 'medium';

generateGraphQLMockData(size)
  .then(() => {
    console.log('\n✓ Done!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n✗ Error:', error);
    process.exit(1);
  });

