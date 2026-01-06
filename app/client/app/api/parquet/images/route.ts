import { NextRequest, NextResponse } from 'next/server';

// Simple mock data based on the parquet structure
const mockImages = [
  {
    sha256: 'f192eaa72dfbc40c7bff22cb04103882fb43d85d780dc587e73f6d8301f8972e',
    local_path: 'cache/imageboard/images/f192eaa72dfbc40c7bff22cb04103882fb43d85d780dc587e73f6d8301f8972e.jpg',
    relative_path: 'f192eaa72dfbc40c7bff22cb04103882fb43d85d780dc587e73f6d8301f8972e.jpg',
    filename: 'f192eaa72dfbc40c7bff22cb04103882fb43d85d780dc587e73f6d8301f8972e.jpg',
    file_size: 92419,
    file_modified: '2026-01-02T19:48:56.669544',
    cached_at: '2026-01-02T23:47:56.416920'
  },
  {
    sha256: 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
    local_path: 'cache/imageboard/images/a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456.jpg',
    relative_path: 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456.jpg',
    filename: 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456.jpg',
    file_size: 124567,
    file_modified: '2026-01-02T18:23:45.123456',
    cached_at: '2026-01-02T23:47:56.416920'
  }
];

export async function GET() {
  try {
    // For now, return mock data. In a real implementation, this would
    // read from the actual parquet files using a server-side process
    return NextResponse.json(mockImages);
  } catch (error) {
    console.error('Error in images API:', error);
    return NextResponse.json(
      { error: 'Failed to load images data' },
      { status: 500 }
    );
  }
}