// Test the factory directly
async function testFactory() {
  console.log('Testing factory...');
  
  try {
    // Import factory functions
    const { generateFeedPage } = await import('/home/warby/Workspace/Bunny/app/client/src/lib/mock-data/factory.ts');
    
    const page = await generateFeedPage(null, 10);
    
    console.log(`Generated ${page.items.length} items:`);
    
    page.items.forEach((item, index) => {
      console.log(`${index + 1}. [${item.source}] ${item.caption} (${item.mediaUrl})`);
    });
    
  } catch (error) {
    console.error('Error testing factory:', error);
  }
}

testFactory();