# Imageboard Gallery Implementation Options

## Best Approach: Extend Existing Media Platform

You already have a production-ready media-platform with Neo4j, Valkey, and S3. Extending it is the best option.

### Why Extend Media Platform?

**Pros:**
- **Existing infrastructure**: Neo4j, Valkey, MinIO already running
- **Shared services**: One set of Docker services to manage
- **Consistent architecture**: GraphQL API, caching layer already built
- **S3 integration**: Easy to migrate images from cache to MinIO
- **Production ready**: Health checks, monitoring already implemented

**Cons:**
- Requires adding new routes/services to existing codebase
- Mix of media types (need to separate concerns)

### Implementation Plan

#### Phase 1: Imageboard Service (Backend)

**1. Create Imageboard Service**
```javascript
// media-platform/services/imageboardService.js

class ImageboardService {
  constructor(neo4jDriver) {
    this.neo4jDriver = neo4jDriver;
  }

  async getThread(board, threadId) {
    const session = this.neo4jDriver.session();
    try {
      const result = await session.run(`
        MATCH (t:Thread {board: $board, thread_id: $threadId})
        OPTIONAL MATCH (p:Post)-[:IN_THREAD]->(t)
        RETURN t, collect(p) as posts
      `, { board, threadId });
      return result.records[0];
    } finally {
      await session.close();
    }
  }

  async listThreads(board, limit = 20, offset = 0) {
    const session = this.neo4jDriver.session();
    try {
      const result = await session.run(`
        MATCH (t:Thread {board: $board})
        RETURN t
        ORDER BY t.last_crawled_at DESC
        SKIP $offset LIMIT $limit
      `, { board, limit, offset });
      return result.records.map(r => r.get('t').properties);
    } finally {
      await session.close();
    }
  }

  async getThreadImages(board, threadId) {
    const session = this.neo4jDriver.session();
    try {
      const result = await session.run(`
        MATCH (p:Post {subreddit: $board})-[:IN_THREAD]->(t:Thread {thread_id: $threadId})
        WHERE p.url CONTAINS '4cdn.org'
        RETURN p.url as url, p.image_hash as hash, p.title as filename
        ORDER BY p.created_utc ASC
      `, { board, threadId });
      return result.records.map(r => r.toObject());
    } finally {
      await session.close();
    }
  }
}
```

**2. Add Routes to app.js**
```javascript
const { ImageboardService } = require('./services/imageboardService');

const imageboardService = new ImageboardService(neo4jDriver);

// Thread routes
app.get('/api/imageboard/threads/:board', async (req, res) => {
  const { board } = req.params;
  const limit = parseInt(req.query.limit) || 20;
  const offset = parseInt(req.query.offset) || 0;

  const threads = await imageboardService.listThreads(board, limit, offset);
  res.json(threads);
});

app.get('/api/imageboard/threads/:board/:threadId', async (req, res) => {
  const { board, threadId } = req.params;
  const thread = await imageboardService.getThread(board, parseInt(threadId));

  if (!thread) {
    return res.status(404).json({ error: 'Thread not found' });
  }

  res.json(thread);
});

app.get('/api/imageboard/threads/:board/:threadId/images', async (req, res) => {
  const { board, threadId } = req.params;
  const images = await imageboardService.getThreadImages(board, parseInt(threadId));
  res.json(images);
});

// Serve cached images from local filesystem
app.use('/cache/imageboard', express.static('/home/jovyan/workspaces/cache/imageboard'));
```

#### Phase 2: Frontend Gallery (Choose One)

### Option A: Next.js (Recommended - Modern)

**Pros:**
- Server Components for direct file access
- Image optimization built-in
- Great SEO
- React ecosystem
- Can deploy to Vercel or self-host

**Setup:**
```bash
cd media-platform
npx create-next-app@latest gallery
cd gallery
npm install @apollo/client graphql
```

**app/page.tsx:**
```typescript
import { ImageboardGallery } from './components/ImageboardGallery';

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <h1 className="text-4xl font-bold mb-8">Imageboard Gallery</h1>
      <ImageboardGallery board="b" />
    </main>
  );
}
```

**app/components/ImageboardGallery.tsx:**
```typescript
'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';

interface Thread {
  thread_id: number;
  title: string;
  post_count: number;
  last_crawled_at: string;
}

export function ImageboardGallery({ board }: { board: string }) {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedThread, setSelectedThread] = useState<number | null>(null);

  useEffect(() => {
    fetch(`/api/imageboard/threads/${board}`)
      .then(res => res.json())
      .then(setThreads);
  }, [board]);

  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="col-span-1 border-r pr-4">
        <h2 className="text-xl font-semibold mb-4">Threads</h2>
        <ul>
          {threads.map(thread => (
            <li
              key={thread.thread_id}
              className="mb-2 cursor-pointer hover:bg-gray-100 p-2"
              onClick={() => setSelectedThread(thread.thread_id)}
            >
              {thread.title || 'No subject'}
              <div className="text-sm text-gray-600">
                {thread.post_count} posts
              </div>
            </li>
          ))}
        </ul>
      </div>
      <div className="col-span-3">
        {selectedThread && <ThreadView board={board} threadId={selectedThread} />}
      </div>
    </div>
  );
}
```

### Option B: Vue 3 (Simpler)

**Setup:**
```bash
cd media-platform
npm create vite@latest gallery -- --template vue
cd gallery
npm install axios
```

**src/App.vue:**
```vue
<template>
  <div class="gallery">
    <h1>Imageboard Gallery</h1>
    <div class="layout">
      <div class="threads">
        <ThreadList :board="board" @select="selectThread" />
      </div>
      <div class="content">
        <ThreadView v-if="selectedThread" :board="board" :threadId="selectedThread" />
      </div>
    </div>
  </div>
</template>
```

### Option C: Static HTML/JS (Fastest)

**Create static gallery generator:**

```bash
# Create a script to generate static HTML
python scripts/generate_gallery.py
# Output to media-platform/public/gallery/
```

**gallery.html:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>Imageboard Gallery</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
  <div id="app" class="container mx-auto p-8">
    <!-- Loaded dynamically -->
  </div>
  <script src="/gallery/index.js"></script>
</body>
</html>
```

#### Phase 3: Image Migration to MinIO

**Optional but recommended for production:**

```javascript
// scripts/migrate-images-to-minio.js

const fs = require('fs');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');

const s3 = new S3Client({
  endpoint: process.env.MINIO_ENDPOINT,
  credentials: {
    accessKeyId: process.env.MINIO_ACCESS_KEY,
    secretAccessKey: process.env.MINIO_SECRET_KEY,
  },
  forcePathStyle: true,
});

async function migrateImage(localPath, s3Key) {
  const content = fs.readFileSync(localPath);
  await s3.send(new PutObjectCommand({
    Bucket: 'imageboard',
    Key: s3Key,
    Body: content,
  }));
}

// Migrate all images from cache/imageboard/images/
```

#### Phase 4: Deployment

**Using existing Docker setup:**

```dockerfile
# media-platform/Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

**Update docker-compose.yml:**
```yaml
services:
  app:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - ./cache/imageboard:/app/cache/imageboard:ro
    environment:
      - NODE_ENV=production
```

## Alternative Options

### Option 2: FastAPI + React (Separate Backend)

**Pros:**
- Clean separation of concerns
- Use Python for API (you're already using it for crawling)
- Fast, type-safe API

**Cons:**
- Additional service to manage
- Duplicate Neo4j connections

### Option 3: Pure Static Site Generator

**Pros:**
- No backend needed after generation
- Fast, simple to deploy
- Can host on GitHub Pages

**Cons:**
- Need to regenerate on updates
- No dynamic features
- Harder to implement search

### Option 4: Jupyter Dashboard

**Pros:**
- Use existing Jupyter setup
- Quick prototype
- Interactive widgets

**Cons:**
- Not production ready
- Poor performance for large galleries
- Limited UX

## Recommended Stack

**Best Value: Next.js + Existing Media Platform**

1. **Backend**: Extend media-platform with imageboard routes
2. **Frontend**: Next.js with Server Components
3. **Images**: Serve from local filesystem (Phase 1), migrate to MinIO (Phase 2)
4. **Database**: Use existing Neo4j
5. **Cache**: Use existing Valkey

**Migration Path:**

```
Phase 1: Static image serving from /cache/imageboard
Phase 2: Migrate to MinIO S3 storage
Phase 3: Add image optimization/variants
Phase 4: Add search/filtering
Phase 5: Add authentication/user accounts
```

## Quick Start Commands

```bash
# Option 1: Next.js gallery
cd media-platform
npx create-next-app@latest gallery
cd gallery
npm install
npm run dev

# Option 2: Extend existing app.js
cd media-platform
# Add imageboard routes to app.js
npm run dev

# Option 3: Static generator
python scripts/generate_gallery.py
# Serve with: python -m http.server 8000
```

## Next Steps

1. **Choose frontend framework**: Next.js (recommended) or Vue
2. **Create imageboard service**: Add to media-platform/services/
3. **Add routes**: Update app.js with imageboard endpoints
4. **Build frontend**: Create gallery UI
5. **Test**: Verify image serving from cache
6. **Optimize**: Add caching, image optimization
7. **Deploy**: Update Docker setup
