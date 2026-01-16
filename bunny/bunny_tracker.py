#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

CONFIG_PATH = Path(__file__).parent.parent / "config" / "bunny_config.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def search_graph_posts(neo4j, config):
    subreddits = [s["name"] for s in config["subreddits"]]
    hours = config["settings"]["hours_to_lookback"]
    
    print(f"📊 Querying Neo4j for posts in: {', '.join(subreddits)}")
    print(f"⏱ Lookback: {hours} hours")
    print(f"📅 Cutoff: {(datetime.utcnow() - timedelta(hours=hours)).isoformat()}\n")
    
    all_results = []
    
    for subreddit in subreddits:
        query = """
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
        WHERE datetime(p.created_utc) >= datetime($cutoff)
        """
        
        params = {"subreddit": subreddit, "cutoff": (datetime.utcnow() - timedelta(hours=hours)).isoformat()}
        
        query += """
        RETURN p.id as id, p.title as title, p.url as url, 
               p.author as author, p.score as score,
               p.created_utc as created, p.subreddit as subreddit
        ORDER BY p.created_utc DESC
        LIMIT 50
        """
        
        try:
            posts = neo4j.execute_read(query, parameters=params)
            for record in posts:
                all_results.append(dict(record))
        except Exception as e:
            print(f"Error querying r/{subreddit}: {e}")
    
    return all_results

def display_results(results, config):
    keywords = []
    for s in config["subreddits"]:
        keywords.extend(s.get("keywords", []))
    
    print("=" * 80)
    print(f"📊 FOUND {len(results)} POSTS IN TRACKED SUBREDDITS")
    print("=" * 80)
    
    for post in results:
        title_lower = post.get("title", "").lower()
        matches = [kw for kw in keywords if kw.lower() in title_lower]
        
        created = post.get("created", "N/A")
        title = post.get("title", "N/A")
        url = post.get("url", "N/A")
        subreddit = post.get("subreddit", "N/A")
        score = post.get("score", 0)
        author = post.get("author", "N/A")
        
        print(f"[{created}] r/{subreddit} | ⬆ {score} | u/{author}")
        if matches:
            print(f"  🔍 {title}")
            print(f"  🏷 Matches: {', '.join(matches)}")
        else:
            print(f"  {title}")
        print(f"  {url}\n")

def main():
    config = load_config()
    print("=" * 80)
    print(f"🐰 BUNNY TRACKER v{config['version']} - {config['name'].upper()}")
    print("=" * 80)
    
    neo4j = get_connection()
    print(f"🔗 Connected to Neo4j: {neo4j.uri}")
    print(f"📁 Config: {CONFIG_PATH}\n")
    
    results = search_graph_posts(neo4j, config)
    display_results(results, config)
    
    neo4j.close()
    
    print("=" * 80)
    print(f"✅ Complete! Found {len(results)} total posts across tracked subreddits")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
