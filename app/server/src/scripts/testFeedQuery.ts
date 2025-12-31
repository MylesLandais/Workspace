import 'dotenv/config';
import { getSession } from '../neo4j/driver.js';

async function main() {
  const session = getSession();

  try {
    // Test simple Media query
    const mediaResult = await session.run(`
      MATCH (m:Media)
      RETURN m.id as id, m.url as url, m.mime_type as mimeType
      LIMIT 5
    `);

    console.log('Media nodes:');
    mediaResult.records.forEach(record => {
      console.log('  -', record.get('id'), record.get('mimeType'));
    });

    // Test Media with Post relationship
    const postResult = await session.run(`
      MATCH (m:Media)-[:APPEARED_IN]->(p:Post)
      RETURN m.id as mediaId, p.id as postId, p.title as title
      LIMIT 5
    `);

    console.log('\nMedia-Post relationships:');
    postResult.records.forEach(record => {
      console.log('  -', record.get('mediaId'), '->', record.get('postId'));
      console.log('    Title:', record.get('title'));
    });

    // Test the feed query pattern
    const feedResult = await session.run(`
      MATCH (m:Media)
      WHERE m.mime_type IS NOT NULL
        AND (m.mime_type STARTS WITH 'image/' OR m.mime_type STARTS WITH 'video/')
      OPTIONAL MATCH (m)-[:APPEARED_IN]->(p:Post)
      RETURN m.id as mediaId, p.id as postId, m.url as url
      LIMIT 5
    `);

    console.log('\nFeed query pattern:');
    feedResult.records.forEach(record => {
      console.log('  - Media:', record.get('mediaId'));
      console.log('    Post:', record.get('postId'));
      console.log('    URL:', record.get('url').substring(0, 80) + '...');
    });

  } finally {
    await session.close();
    process.exit(0);
  }
}

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
