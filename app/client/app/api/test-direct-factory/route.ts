import { NextRequest, NextResponse } from 'next/server';
import { generateFeedPage } from '@/lib/mock-data/factory';

export async function GET() {
  try {
    console.log('DIRECT FACTORY TEST: Calling generateFeedPage directly...');
    
    const page = await generateFeedPage(null, 20);
    
    console.log(`DIRECT FACTORY TEST: Generated ${page.items.length} items`);
    
    const sample = page.items.slice(0, 10).map(item => ({
      id: item.id,
      source: item.source,
      caption: item.caption,
      mediaUrl: item.mediaUrl
    }));
    
    return NextResponse.json({
      total: page.items.length,
      sample,
      hasNextPage: page.hasNextPage,
      allItems: page.items.map(item => ({
        id: item.id,
        source: item.source,
        mediaUrl: item.mediaUrl
      }))
    });
  } catch (error) {
    console.error('DIRECT FACTORY TEST: Error:', error);
    return NextResponse.json(
      { error: 'Failed to test factory directly', details: error.message },
      { status: 500 }
    );
  }
}