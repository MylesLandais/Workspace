"""GraphQL server for feed monitoring."""

import sys
from pathlib import Path

# Add src to path (same as web server)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from feed.graphql.schema import create_graphql_router

app = FastAPI(title="Feed Monitor GraphQL API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create GraphQL router
graphql_router = create_graphql_router()

# Mount GraphQL endpoint
app.include_router(graphql_router, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Feed Monitor GraphQL API",
        "graphql_endpoint": "/graphql",
        "graphql_playground": "/graphql (use GraphQL Playground or Apollo Studio)",
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Starting Feed Monitor GraphQL Server")
    print("=" * 60)
    print("GraphQL endpoint: http://localhost:8001/graphql")
    print("WebSocket subscriptions: ws://localhost:8001/graphql")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

