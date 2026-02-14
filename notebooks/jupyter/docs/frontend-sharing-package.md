# Frontend Team Sharing Package

## Quick Share Checklist

Share these files with your frontend/UX team:

### ✅ Must Share (Essential)

1. **`docs/FEED_GRAPHQL_API.md`**
   - Complete API documentation
   - Query examples
   - Subscription examples
   - Client code samples

2. **`src/feed/graphql/mock_data.py`**
   - Real mock data from collected posts
   - 20 posts total (10 per subreddit)
   - All image URLs included
   - Ready to use in development

3. **`examples/graphql_client_example.html`**
   - Working example implementation
   - Shows how to connect and query
   - Demonstrates subscriptions
   - Can be opened directly in browser

### 📋 Nice to Have (Recommended)

4. **`src/feed/graphql/schema.py`**
   - GraphQL schema source code
   - Type definitions
   - Useful for generating TypeScript types

5. **`QUICKSTART_GRAPHQL.md`**
   - Quick setup instructions
   - How to start the server
   - Test commands

6. **`src/feed/models/post.py`**
   - Post data model
   - Field definitions
   - Type information

## How to Share

### Option 1: Create a ZIP Package
```bash
# Create a frontend package
mkdir -p frontend_package
cp docs/FEED_GRAPHQL_API.md frontend_package/
cp src/feed/graphql/mock_data.py frontend_package/
cp examples/graphql_client_example.html frontend_package/
cp QUICKSTART_GRAPHQL.md frontend_package/
zip -r frontend_package.zip frontend_package/
```

### Option 2: Share via Git
Create a branch or tag:
```bash
git tag frontend-v1.0
git push origin frontend-v1.0
```

### Option 3: Share Individual Files
Just send the 3 essential files listed above.

## What Frontend Teams Need to Know

### 1. API Endpoint
- GraphQL: `http://localhost:8001/graphql`
- WebSocket: `ws://localhost:8001/graphql`

### 2. Key Data Fields
- Posts have `is_image` boolean
- Posts have `image_url` for direct image links
- Posts have `subreddit`, `score`, `num_comments`, etc.

### 3. Mock Data
- 20 posts total
- 2 subreddits: BrookeMonkTheSecond, BestOfBrookeMonk
- All posts are images (either direct or galleries)

### 4. Real-time Updates
- Use GraphQL subscriptions
- WebSocket connection required
- Updates every 5 seconds

## Example Mock Data Structure

```json
{
  "id": "anc6w05ekr8g1",
  "title": "Brooke monk",
  "score": 7,
  "num_comments": 1,
  "url": "https://i.redd.it/anc6w05ekr8g1.jpeg",
  "image_url": "https://i.redd.it/anc6w05ekr8g1.jpeg",
  "is_image": true,
  "subreddit": "BrookeMonkTheSecond",
  "author": "letsgoon45",
  "created_utc": "2025-12-22T08:14:39Z"
}
```

## Next Steps for Frontend Team

1. Read `docs/FEED_GRAPHQL_API.md` for API details
2. Use `mock_data.py` for development
3. Reference `graphql_client_example.html` for implementation
4. Set up GraphQL client (Apollo, urql, etc.)
5. Start building UI components

## Support

- API questions: See `docs/FEED_GRAPHQL_API.md`
- Implementation: See `examples/graphql_client_example.html`
- Schema: See `src/feed/graphql/schema.py`







