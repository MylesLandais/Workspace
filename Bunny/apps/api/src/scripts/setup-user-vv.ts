import mysql from "mysql2/promise";
import neo4j from "neo4j-driver";
import crypto from "crypto";

async function setupVv() {
  // MySQL connection
  const mysqlConn = await mysql.createConnection({
    host: process.env.MYSQL_HOST || "localhost",
    user: "root",
    password: "",
    database: process.env.MYSQL_DATABASE || "bunny_auth",
  });

  // Neo4j connection
  // Try 'password' from docker-compose.yml
  const driver = neo4j.driver(
    "bolt://localhost:7687",
    neo4j.auth.basic("neo4j", "password"),
  );

  try {
    const email = "vv@example.com";
    console.log(`Searching for user with email: ${email}`);

    const [users] = (await mysqlConn.execute(
      "SELECT id, email, name FROM user WHERE email = ?",
      [email],
    )) as any;

    if (users.length === 0) {
      console.error(`User with email ${email} not found.`);
      process.exit(1);
    }

    const vv = users[0];
    console.log(`Found user vv: ${vv.id}`);

    const session = driver.session();
    try {
      // 1. Create/get FeedGroup
      const groupId = `${vv.id}-default`;
      const groupName = "My Subreddits";

      console.log(`Ensuring FeedGroup exists: ${groupName} (${groupId})`);
      await session.run(
        `
        MERGE (fg:FeedGroup {id: $groupId})
        ON CREATE SET 
          fg.name = $groupName,
          fg.userId = $userId,
          fg.created_at = datetime()
        ON MATCH SET
          fg.userId = $userId
        RETURN fg
      `,
        { groupId, groupName, userId: vv.id },
      );

      // 2. Add default sources
      const defaultSubreddits = ["BunnyGirls", "unixporn"];
      for (const sub of defaultSubreddits) {
        console.log(`Creating source for r/${sub}...`);
        const sourceId = crypto.randomUUID();

        await session.run(
          `
          MERGE (s:Subreddit {name: $subredditName})
          ON CREATE SET
            s.display_name = $subredditName,
            s.subscribers = 0,
            s.created_at = datetime()
          
          CREATE (source:Source {
            id: $sourceId,
            name: $subredditName,
            source_type: 'reddit',
            subreddit_name: $subredditName,
            is_paused: false,
            is_enabled: true,
            media_count: 0,
            created_at: datetime()
          })
          
          WITH source, s
          MATCH (fg:FeedGroup {id: $groupId})
          CREATE (fg)-[:CONTAINS]->(source)
          CREATE (source)-[:POSTED_IN]->(s)
          RETURN source
        `,
          {
            subredditName: sub,
            groupId,
            sourceId,
          },
        );
        console.log(`Created source for r/${sub}`);
      }

      console.log("Setup completed successfully!");
    } finally {
      await session.close();
    }
  } catch (error) {
    console.error("Setup failed with error:", error);
    process.exit(1);
  } finally {
    await mysqlConn.end();
    await driver.close();
  }
}

setupVv();
