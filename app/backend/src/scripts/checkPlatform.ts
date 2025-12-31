import 'dotenv/config';
import { getSession } from '../neo4j/driver.js';

async function main() {
  const session = getSession();

  try {
    // Check what's in the Handle nodes
    const handleResult = await session.run(`
      MATCH (h:Handle)
      RETURN h.platform as platform, h.handle as handle, h.username as username
      LIMIT 5
    `);

    console.log('Handle nodes:');
    handleResult.records.forEach(record => {
      console.log('  Platform:', record.get('platform'));
      console.log('  Handle:', record.get('handle'));
      console.log('  Username:', record.get('username'));
      console.log('');
    });

    // Check User nodes
    const userResult = await session.run(`
      MATCH (u:User)
      RETURN u.username as username
      LIMIT 5
    `);

    console.log('User nodes:');
    userResult.records.forEach(record => {
      console.log('  Username:', record.get('username'));
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
