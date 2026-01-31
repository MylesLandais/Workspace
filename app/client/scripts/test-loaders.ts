import { generateParquetFeed } from "../src/lib/mock-data/parquet-loader";
import { generateImageboardFeed } from "../src/lib/mock-data/imageboard-loader";

async function testLoaders() {
  console.log("=== Testing Loaders ===\n");

  console.log("Testing parquet feed...");
  try {
    const parquetItems = await generateParquetFeed();
    console.log(`Parquet: ${parquetItems.length} items`);
    if (parquetItems.length > 0) {
      console.log("Sample:", parquetItems[0].mediaUrl);
    }
  } catch (error) {
    console.error("Parquet error:", error);
  }

  console.log("\nTesting imageboard feed...");
  try {
    const imageboardItems = await generateImageboardFeed();
    console.log(`Imageboard: ${imageboardItems.length} items`);
    if (imageboardItems.length > 0) {
      console.log("Sample:", imageboardItems[0].mediaUrl);
    }
  } catch (error) {
    console.error("Imageboard error:", error);
  }
}

testLoaders();
