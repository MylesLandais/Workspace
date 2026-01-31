import { generateImageboardFeed } from "/home/warby/Workspace/Bunny/app/client/src/lib/mock-data/imageboard-loader.js";

// Test the imageboard loader directly
async function testImageboardLoader() {
  try {
    console.log("Testing imageboard loader...");
    const feed = await generateImageboardFeed();
    console.log(`Generated ${feed.length} imageboard items`);

    if (feed.length > 0) {
      console.log("Sample item:", {
        id: feed[0].id,
        source: feed[0].source,
        caption: feed[0].caption,
        mediaUrl: feed[0].mediaUrl,
        imageCount: feed[0].imageCount,
      });
    }
  } catch (error) {
    console.error("Error testing imageboard loader:", error);
  }
}

testImageboardLoader();
