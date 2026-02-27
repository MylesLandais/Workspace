#!/usr/bin/env python3
"""Generate visual dependency graph using Graphviz."""

import sys
from pathlib import Path

graphviz_code = """
digraph YouTubeFeedDependencies {
    rankdir=TB;
    node [shape=box, style=rounded, fontname="Arial"];
    edge [fontname="Arial"];
    
    // External Dependencies
    subgraph cluster_externals {
        label = "External Dependencies";
        style = dashed;
        
        yt_dlp [label="yt-dlp", style="filled", fillcolor="lightblue"];
        youtube_api [label="YouTube API", shape=ellipse, style="filled", fillcolor="lightgray"];
        neo4j_driver [label="neo4j driver", style="filled", fillcolor="lightgreen"];
        redis_driver [label="redis driver", style="filled", fillcolor="lightcoral"];
        fastapi [label="FastAPI", style="filled", fillcolor="lightyellow"];
        pydantic [label="Pydantic", style="filled", fillcolor="lightyellow"];
        python_dotenv [label="python-dotenv", style="filled", fillcolor="lightyellow"];
    }
    
    // Storage Layer
    subgraph cluster_storage {
        label = "Storage Layer";
        style = filled;
        fillcolor = "lightgray";
        
        neo4j_connection [label="Neo4j Connection"];
        valkey_connection [label="Valkey/Redis Connection"];
    }
    
    // Service Layer
    subgraph cluster_services {
        label = "Service Layer";
        style = filled;
        fillcolor = "lightgray";
        
        youtube_enhanced_service [label="YouTube Enhanced Service"];
        youtube_analytics_service [label="YouTube Analytics Service"];
        comment_thread_service [label="Comment Thread Service"];
        youtube_subscription_service [label="YouTube Subscription Service"];
    }
    
    // API Layer
    subgraph cluster_api {
        label = "API Layer";
        style = filled;
        fillcolor = "lightgray";
        
        youtube_enhanced_api [label="YouTube Enhanced API"];
        youtube_analytics_api [label="YouTube Analytics API"];
    }
    
    // Worker Layer
    subgraph cluster_workers {
        label = "Worker Layer";
        style = filled;
        fillcolor = "lightgray";
        
        youtube_polling_worker [label="YouTube Polling Worker"];
        youtube_channel_crawler [label="YouTube Channel Crawler"];
    }
    
    // Model Layer
    subgraph cluster_models {
        label = "Model Layer";
        style = filled;
        fillcolor = "lightgray";
        
        creator_model [label="Creator Model"];
        handle_model [label="Handle Model"];
        platform_model [label="Platform Model"];
        ontology_schema [label="Ontology Schema"];
    }
    
    // Standard Library
    subgraph cluster_stdlib {
        label = "Standard Library";
        style = dotted;
        
        os [label="os"];
        sys [label="sys"];
        json [label="json"];
        subprocess [label="subprocess"];
        pathlib [label="pathlib"];
        datetime [label="datetime"];
        uuid [label="uuid"];
        typing [label="typing"];
        collections [label="collections"];
        logging [label="logging"];
        time [label="time"];
    }
    
    // External Dependencies Relationships
    yt_dlp -> youtube_api [label="fetches from"];
    neo4j_connection -> neo4j_driver [label="uses"];
    valkey_connection -> redis_driver [label="uses"];
    
    // Storage Layer Dependencies
    youtube_enhanced_service -> neo4j_connection [label="imports"];
    youtube_analytics_service -> neo4j_connection [label="imports"];
    comment_thread_service -> neo4j_connection [label="imports"];
    youtube_subscription_service -> neo4j_connection [label="imports"];
    youtube_subscription_service -> valkey_connection [label="imports"];
    
    // Service Layer Dependencies
    youtube_polling_worker -> youtube_enhanced_service [label="imports"];
    youtube_polling_worker -> neo4j_connection [label="imports"];
    youtube_channel_crawler -> youtube_subscription_service [label="imports"];
    
    // API Layer Dependencies
    youtube_enhanced_api -> neo4j_connection [label="imports"];
    youtube_enhanced_api -> fastapi [label="uses"];
    youtube_enhanced_api -> pydantic [label="uses"];
    youtube_enhanced_api -> json [label="uses"];
    
    youtube_analytics_api -> youtube_analytics_service [label="imports"];
    youtube_analytics_api -> comment_thread_service [label="imports"];
    youtube_analytics_api -> fastapi [label="uses"];
    youtube_analytics_api -> pydantic [label="uses"];
    
    // Model Layer Dependencies
    youtube_subscription_service -> creator_model [label="imports"];
    youtube_subscription_service -> handle_model [label="imports"];
    youtube_subscription_service -> platform_model [label="imports"];
    youtube_subscription_service -> ontology_schema [label="imports"];
    
    // Standard Library Dependencies
    youtube_enhanced_service -> subprocess [label="uses"];
    youtube_enhanced_service -> json [label="uses"];
    youtube_polling_worker -> logging [label="uses"];
    youtube_polling_worker -> time [label="uses"];
    
    // External Config
    youtube_subscription_service -> python_dotenv [label="imports"];
    
    // Data Flow
    youtube_enhanced_service -> yt_dlp [label="calls via", style=dashed, color=red];
    
    // Layout adjustments
    { rank = same; neo4j_connection; valkey_connection; }
    { rank = same; youtube_enhanced_service; youtube_analytics_service; comment_thread_service; youtube_subscription_service; }
    { rank = same; youtube_enhanced_api; youtube_analytics_api; youtube_polling_worker; }
    { rank = same; creator_model; handle_model; platform_model; ontology_schema; }
}
"""

output_file = Path(__file__).parent / "dependency_graph.dot"
with open(output_file, "w") as f:
    f.write(graphviz_code)

print(f"Generated dependency graph: {output_file}")
print("\nTo visualize, install Graphviz and run:")
print(f"  dot -Tpng {output_file} -o dependency_graph.png")
print(f"  open dependency_graph.png")
