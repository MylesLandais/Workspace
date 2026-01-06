import { NextRequest, NextResponse } from 'next/server';

// Simple mock data based on the parquet structure
const mockThreads = [
  {
    board: 'b',
    thread_id: '944348635',
    url: 'https://boards.4chan.org/b/thread/944348635',
    title: 'Post zillenial girls in their natural habitat',
    post_count: 2,
    image_count: 2,
    html_path: 'cache/imageboard/html/b_944348635.html',
    html_filename: 'b_944348635.html',
    file_size: 17219,
    file_modified: '2026-01-02T21:05:16.293525',
    cached_at: '2026-01-02T23:47:48.402500'
  },
  {
    board: 'b',
    thread_id: '944303266',
    url: 'https://boards.4chan.org/b/thread/944303266',
    title: 'WebM thread: Post your favorite animations',
    post_count: 150,
    image_count: 45,
    html_path: 'cache/imageboard/html/b_944303266.html',
    html_filename: 'b_944303266.html',
    file_size: 45678,
    file_modified: '2026-01-02T19:30:22.123456',
    cached_at: '2026-01-02T23:47:48.402500'
  },
  {
    board: 'b',
    thread_id: '944330306',
    url: 'https://boards.4chan.org/b/thread/944330306',
    title: 'YLYL - You Laugh You Lose',
    post_count: 89,
    image_count: 23,
    html_path: 'cache/imageboard/html/b_944330306.html',
    html_filename: 'b_944330306.html',
    file_size: 31245,
    file_modified: '2026-01-02T20:15:44.987654',
    cached_at: '2026-01-02T23:47:48.402500'
  }
];

export async function GET() {
  try {
    // For now, return mock data. In a real implementation, this would
    // read from the actual parquet files using a server-side process
    return NextResponse.json(mockThreads);
  } catch (error) {
    console.error('Error in threads API:', error);
    return NextResponse.json(
      { error: 'Failed to load threads data' },
      { status: 500 }
    );
  }
}