/**
 * Import additional Reddit subscriptions from custom feed (favs)
 *
 * Usage: bun run src/scripts/import-reddit-favs.ts
 */
import { getSession, createIndexes } from "../neo4j/driver.js";
import {
  findOrCreateSource,
  bulkSubscribe,
} from "../neo4j/queries/subscriptions.js";
import mysql from "mysql2/promise";
import dotenv from "dotenv";
import path from "path";

// Load env from project root
const projectRoot = path.resolve(process.cwd(), "..", "..");
dotenv.config({ path: path.join(projectRoot, ".env") });

// Additional subreddits from custom-feed-community-list (favs)
const SUBREDDITS = [
  "AddisonRae",
  "AliceEve",
  "AnadeArmas",
  "AnneHathaway",
  "AnyaTaylorJoy",
  "BarbaraPalvin",
  "BotezLive",
  "BrecBassinger",
  "BrittanySnow",
  "BunnyGirls",
  "Celebs",
  "ChloeBennet",
  "ClaireHolt2",
  "DanielleCampbell",
  "DoutzenKroes",
  "ElleFanning",
  "ElsaHosk",
  "EmmaWatson",
  "EmmyRossum",
  "EricaLindbeck",
  "ErinHeatherton",
  "Florence_Pugh",
  "GWNerdy",
  "GalGadot",
  "GirlsfromChess",
  "HannahBeast",
  "HazelGraye",
  "HermioneCorfield",
  "HogwartsGoneWild",
  "JenniferLawrence",
  "Josephine_Skriver",
  "KatDennings",
  "KatrinaBowden",
  "KiraKosarin",
  "KiraKosarinLewd",
  "LeightonMeester",
  "MargotRobbie",
  "MarinKitagawaR34",
  "McKaylaMaroney",
  "MelissaBenoist",
  "MinkaKelly",
  "MirandaKerr",
  "Models",
  "NatalieDormer",
  "NinaDobrev",
  "Nina_Agdal",
  "OfflinetvGirls",
  "OliviaRodrigoNSFW",
  "OneTrueMentalOut",
  "OvileeWorship",
  "PhoebeTonkin",
  "Pokimane",
  "PortiaDoubleday",
  "RachelCook",
  "RachelMcAdams",
  "SammiHanratty",
  "SaraSampaio",
  "SarahHyland",
  "SelenaGomez",
  "ShaileneWoodley",
  "StellaMaxwell",
  "SydneySweeney",
  "TOS_girls",
  "TaylorSwift",
  "TaylorSwiftCandids",
  "TaylorSwiftMidriff",
  "Taylorhillfantasy",
  "VanessaHudgens",
  "VolleyballGirls",
  "WatchItForThePlot",
  "angourierice",
  "annakendrick",
  "blakelively",
  "candiceswanepoel",
  "erinmoriartyNEW",
  "haydenpanettiere",
  "howdyhowdyyallhot",
  "islafisher",
  "jenniferlovehewitt",
  "jessicaalba",
  "karliekloss",
  "kateupton",
  "kayascodelario",
  "kristenbell",
  "kristinefroseth",
  "lizgillies",
  "milanavayntrub",
  "natalieportman",
  "oliviadunne",
  "sophieturner",
  "sunisalee",
  "victoriajustice",
  "victorious",
  "vsangels",
];

const USER_EMAIL = "vv@example.com";

async function main() {
  console.log(
    `Importing ${SUBREDDITS.length} additional Reddit subscriptions for ${USER_EMAIL}`,
  );

  // Connect to MySQL to get user ID
  const pool = mysql.createPool({
    host: process.env.MYSQL_HOST || "127.0.0.1",
    port: parseInt(process.env.MYSQL_PORT || "3307", 10),
    user: process.env.MYSQL_USER || "root",
    password: process.env.MYSQL_PASSWORD || "secret",
    database: process.env.MYSQL_DATABASE || "bunny_auth",
  });

  try {
    // Get user by email
    const [rows] = await pool.query<mysql.RowDataPacket[]>(
      "SELECT id FROM user WHERE email = ?",
      [USER_EMAIL],
    );

    if (rows.length === 0) {
      console.error(`User ${USER_EMAIL} not found in database`);
      process.exit(1);
    }

    const userId = rows[0].id as string;
    console.log(`Found user: ${userId}`);

    // Ensure Neo4j indexes exist
    await createIndexes();

    // Create Source nodes for each subreddit
    console.log("Creating Source nodes in Neo4j...");
    const sourceIds: string[] = [];
    const errors: string[] = [];

    for (const subreddit of SUBREDDITS) {
      try {
        const source = await findOrCreateSource("REDDIT", subreddit, {
          name: `r/${subreddit}`,
        });
        sourceIds.push(source.id);
        process.stdout.write(".");
      } catch (err) {
        errors.push(`${subreddit}: ${err}`);
        process.stdout.write("x");
      }
    }
    console.log("\n");

    if (errors.length > 0) {
      console.log(`Errors creating sources (${errors.length}):`);
      errors.slice(0, 10).forEach((e) => console.log(`  - ${e}`));
      if (errors.length > 10) {
        console.log(`  ... and ${errors.length - 10} more`);
      }
    }

    console.log(`Created/found ${sourceIds.length} Source nodes`);

    // Create SUBSCRIBES_TO relationships in Neo4j
    console.log("Creating subscriptions in Neo4j...");
    const result = await bulkSubscribe(userId, sourceIds);
    console.log(`Subscribed: ${result.subscribed}, Failed: ${result.failed}`);

    // Create subscription records in MySQL
    console.log("Creating subscription records in MySQL...");
    const now = new Date();
    let inserted = 0;
    let skipped = 0;

    for (const sourceId of sourceIds) {
      try {
        const subId = crypto.randomUUID();
        await pool.query(
          `INSERT INTO user_subscription
           (id, user_id, source_id, is_paused, notifications, priority, added_at, created_at, updated_at)
           VALUES (?, ?, ?, 0, 'none', 0, ?, ?, ?)
           ON DUPLICATE KEY UPDATE updated_at = ?`,
          [subId, userId, sourceId, now, now, now, now],
        );
        inserted++;
        process.stdout.write(".");
      } catch (err: any) {
        if (err.code === "ER_DUP_ENTRY") {
          skipped++;
          process.stdout.write("s");
        } else {
          console.error(
            `\nError inserting subscription for ${sourceId}:`,
            err.message,
          );
        }
      }
    }
    console.log("\n");

    console.log(`MySQL: Inserted ${inserted}, Skipped (existing) ${skipped}`);

    console.log("\n=== Import Complete ===");
    console.log(`Total subreddits: ${SUBREDDITS.length}`);
    console.log(`Neo4j sources: ${sourceIds.length}`);
    console.log(`Neo4j subscriptions: ${result.subscribed}`);
    console.log(`MySQL records: ${inserted}`);
  } finally {
    await pool.end();
    const session = getSession();
    await session.close();
  }
}

main().catch(console.error);
