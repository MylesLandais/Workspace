"""FastAPI server for feed monitoring web interface."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional, List
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from feed.storage.neo4j_connection import get_connection

app = FastAPI(title="Feed Monitor", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get Neo4j connection
try:
    neo4j = get_connection()
except Exception as e:
    print(f"Warning: Could not connect to Neo4j: {e}")
    neo4j = None


@app.get("/")
async def root():
    """Serve the main HTML page."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Feed Monitor</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background: #F7F9FB; }
            .glass { backdrop-filter: blur(10px); background: rgba(255, 255, 255, 0.7); }
        </style>
    </head>
    <body class="font-sans">
        <div id="app" class="min-h-screen">
            <nav class="glass border-b border-gray-200 p-4 sticky top-0 z-50">
                <div class="max-w-7xl mx-auto flex justify-between items-center">
                    <h1 class="text-2xl font-bold text-gray-800">Feed Monitor</h1>
                    <div class="flex gap-4">
                        <button onclick="loadStats()" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                            Refresh
                        </button>
                    </div>
                </div>
            </nav>
            
            <main class="max-w-7xl mx-auto p-6">
                <div id="stats" class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <!-- Stats will be loaded here -->
                </div>
                
                <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <h2 class="text-xl font-bold mb-4 text-gray-800">Recent Posts</h2>
                    <div id="posts" class="space-y-4">
                        <!-- Posts will be loaded here -->
                    </div>
                </div>
                
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <h2 class="text-xl font-bold mb-4 text-gray-800">Image Gallery</h2>
                    <div id="gallery" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        <!-- Images will be loaded here -->
                    </div>
                </div>
            </main>
        </div>
        
        <script>
            async function loadStats() {
                try {
                    const [statsRes, postsRes, imagesRes] = await Promise.all([
                        fetch('/api/stats'),
                        fetch('/api/posts?limit=10'),
                        fetch('/api/images?limit=20')
                    ]);
                    
                    const stats = await statsRes.json();
                    const posts = await postsRes.json();
                    const images = await imagesRes.json();
                    
                    // Update stats
                    document.getElementById('stats').innerHTML = `
                        <div class="bg-white rounded-lg shadow-sm p-6">
                            <div class="text-3xl font-bold text-blue-600">${stats.total_posts}</div>
                            <div class="text-gray-600">Total Posts</div>
                        </div>
                        <div class="bg-white rounded-lg shadow-sm p-6">
                            <div class="text-3xl font-bold text-green-600">${stats.subreddits}</div>
                            <div class="text-gray-600">Subreddits</div>
                        </div>
                        <div class="bg-white rounded-lg shadow-sm p-6">
                            <div class="text-3xl font-bold text-purple-600">${stats.users}</div>
                            <div class="text-gray-600">Users</div>
                        </div>
                    `;
                    
                    // Update posts
                    document.getElementById('posts').innerHTML = posts.map(post => `
                        <div class="border-b border-gray-200 pb-4">
                            <div class="flex justify-between items-start">
                                <div class="flex-1">
                                    <h3 class="font-semibold text-gray-800">${post.title}</h3>
                                    <div class="text-sm text-gray-600 mt-1">
                                        r/${post.subreddit} • ${post.score} upvotes • ${post.comments} comments
                                    </div>
                                </div>
                                <div class="text-xs text-gray-500 ml-4">
                                    ${new Date(post.created_utc).toLocaleDateString()}
                                </div>
                            </div>
                        </div>
                    `).join('');
                    
                    // Update gallery
                    document.getElementById('gallery').innerHTML = images.map(img => `
                        <div class="relative group cursor-pointer" onclick="openImage('${img.url}', '${img.title}')">
                            <img src="${img.url}" alt="${img.title}" 
                                 class="w-full h-48 object-cover rounded-lg hover:opacity-90 transition"
                                 loading="lazy" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 400 300%27%3E%3Crect fill=%27%23ddd%27 width=%27400%27 height=%27300%27/%3E%3Ctext x=%2750%25%27 y=%2750%25%27 text-anchor=%27middle%27 dy=%27.3em%27 fill=%27%23999%27%3EImage%3C/text%3E%3C/svg%3E'">
                            <div class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white p-2 rounded-b-lg opacity-0 group-hover:opacity-100 transition">
                                <div class="text-xs truncate">${img.title}</div>
                            </div>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error loading data:', error);
                }
            }
            
            function openImage(url, title) {
                window.open(url, '_blank');
            }
            
            // Load on page load
            loadStats();
            // Auto-refresh every 30 seconds
            setInterval(loadStats, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/stats")
async def get_stats():
    """Get overall statistics."""
    if not neo4j:
        raise HTTPException(status_code=503, detail="Neo4j not connected")
    
    try:
        # Total posts
        query = "MATCH (p:Post) RETURN count(p) as total"
        result = neo4j.execute_read(query)
        total_posts = result[0]["total"] if result else 0
        
        # Subreddits
        query = "MATCH (s:Subreddit) RETURN count(s) as total"
        result = neo4j.execute_read(query)
        subreddits = result[0]["total"] if result else 0
        
        # Users
        query = "MATCH (u:User) RETURN count(u) as total"
        result = neo4j.execute_read(query)
        users = result[0]["total"] if result else 0
        
        return {
            "total_posts": total_posts,
            "subreddits": subreddits,
            "users": users,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts")
async def get_posts(
    limit: int = Query(10, ge=1, le=100),
    subreddit: Optional[str] = None,
    offset: int = Query(0, ge=0),
):
    """Get recent posts."""
    if not neo4j:
        raise HTTPException(status_code=503, detail="Neo4j not connected")
    
    try:
        if subreddit:
            query = """
            MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
            OPTIONAL MATCH (u:User)-[:POSTED]->(p)
            RETURN p.id as id, p.title as title, p.created_utc as created_utc,
                   p.score as score, p.num_comments as comments, p.upvote_ratio as ratio,
                   p.url as url, s.name as subreddit, u.username as author
            ORDER BY p.created_utc DESC
            SKIP $offset
            LIMIT $limit
            """
            params = {"subreddit": subreddit, "offset": offset, "limit": limit}
        else:
            query = """
            MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
            OPTIONAL MATCH (u:User)-[:POSTED]->(p)
            RETURN p.id as id, p.title as title, p.created_utc as created_utc,
                   p.score as score, p.num_comments as comments, p.upvote_ratio as ratio,
                   p.url as url, s.name as subreddit, u.username as author
            ORDER BY p.created_utc DESC
            SKIP $offset
            LIMIT $limit
            """
            params = {"offset": offset, "limit": limit}
        
        result = neo4j.execute_read(query, parameters=params)
        posts = [dict(record) for record in result]
        
        # Convert datetime objects to strings
        for post in posts:
            if hasattr(post.get("created_utc"), "isoformat"):
                post["created_utc"] = post["created_utc"].isoformat()
        
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images")
async def get_images(
    limit: int = Query(20, ge=1, le=100),
    subreddit: Optional[str] = None,
):
    """Get image posts."""
    if not neo4j:
        raise HTTPException(status_code=503, detail="Neo4j not connected")
    
    try:
        if subreddit:
            query = """
            MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
            WHERE p.url CONTAINS 'i.redd.it' OR p.url CONTAINS 'reddit.com/gallery'
            RETURN p.id as id, p.title as title, p.url as url, p.score as score,
                   s.name as subreddit, p.created_utc as created_utc
            ORDER BY p.created_utc DESC
            LIMIT $limit
            """
            params = {"subreddit": subreddit, "limit": limit}
        else:
            query = """
            MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
            WHERE p.url CONTAINS 'i.redd.it' OR p.url CONTAINS 'reddit.com/gallery'
            RETURN p.id as id, p.title as title, p.url as url, p.score as score,
                   s.name as subreddit, p.created_utc as created_utc
            ORDER BY p.created_utc DESC
            LIMIT $limit
            """
            params = {"limit": limit}
        
        result = neo4j.execute_read(query, parameters=params)
        images = [dict(record) for record in result]
        
        # Convert datetime objects to strings
        for img in images:
            if hasattr(img.get("created_utc"), "isoformat"):
                img["created_utc"] = img["created_utc"].isoformat()
        
        return images
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subreddits")
async def get_subreddits():
    """Get list of subreddits with post counts."""
    if not neo4j:
        raise HTTPException(status_code=503, detail="Neo4j not connected")
    
    try:
        query = """
        MATCH (s:Subreddit)
        OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
        RETURN s.name as name, count(p) as post_count
        ORDER BY post_count DESC
        """
        result = neo4j.execute_read(query)
        subreddits = [dict(record) for record in result]
        return subreddits
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Starting Feed Monitor Web Server")
    print("=" * 60)
    print(f"Server will be available at: http://localhost:8000")
    print(f"API docs at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

