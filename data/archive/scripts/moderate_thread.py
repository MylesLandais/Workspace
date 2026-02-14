import sys
import re
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection
from feed.services.bot_pattern_detector import BotPatternDetector

def identify_crap_posts(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify 'crap' posts based on patterns."""
    crap_posts = []
    
    # Hex pattern (long random-looking strings)
    hex_pattern = re.compile(r'[0-9a-f]{16,}')
    
    # Bot identifiers mentioned in thread
    bot_keywords = ["logfag", "shiteater", "douchebag"]
    
    for post in posts:
        text = post.get("text", "").lower()
        post_no = post.get("no")
        
        is_crap = False
        reason = ""
        
        # 1. Hex/random strings
        if hex_pattern.search(text):
            is_crap = True
            reason = "bot: hex/random strings"
            
        # 2. Known bot identifiers/keywords (if they are the main content)
        elif any(kw in text for kw in bot_keywords) and len(text) < 50:
            # Note: Sometimes these are used in replies to bots, 
            # but if they are the ONLY content, it might be noise.
            # However, the user said "tagged for bot and low-quality noise".
            pass
            
        # 3. Repetitive patterns (e.g., "nut after nut after nut")
        if "nut after nut after" in text:
            is_crap = True
            reason = "low-quality: repetitive noise"
            
        # 4. Very short repetitive noise
        if text.strip() in ["uh oh", "wow", "based, ngl"]:
            # These are low quality but maybe not "crap" enough to hide 
            # unless the volume is very high. 
            pass

        if is_crap:
            crap_posts.append({
                "post_no": post_no,
                "reason": reason,
                "text": text[:100]
            })
            
    return crap_posts

def mark_hidden_in_neo4j(board: str, thread_id: str, post_nos: List[str], reason: str):
    """Mark posts as hidden in Neo4j."""
    neo4j = get_connection()
    
    query = """
    UNWIND $post_nos as post_no
    MATCH (p:Post {id: $board + "_" + $thread_id + "_" + post_no})
    SET p.hidden = true,
        p.moderation_reason = $reason,
        p.hidden_flag = 'tagged for bot and low-quality noise',
        p.updated_at = datetime()
    RETURN count(p) as marked_count
    """
    
    result = neo4j.execute_write(
        query,
        parameters={
            "board": board,
            "thread_id": thread_id,
            "post_nos": post_nos,
            "reason": reason
        }
    )
    return result[0]["marked_count"] if result else 0

if __name__ == "__main__":
    # The specific thread from the request
    board = "b"
    thread_id = "944358701"
    
    # In a real scenario, we'd fetch from Neo4j or 4chan API
    # For this task, I'll use the data I saw in webfetch
    posts = [
        {"no": "944359498", "text": "05b3a2767b4bfe6f9e5171aa9 d23bef5dc6ddfac75a2159 d13060dcef05d7e4236"},
        {"no": "944359013", "text": "Nut after nut after nut after nut after"},
        # Add more if needed
    ]
    
    crap_posts = identify_crap_posts(posts)
    
    if crap_posts:
        print(f"Identified {len(crap_posts)} crap posts")
        for cp in crap_posts:
            print(f"  Post {cp['post_no']}: {cp['reason']}")
            
        post_nos = [cp["post_no"] for cp in crap_posts]
        marked = mark_hidden_in_neo4j(board, thread_id, post_nos, "bot and low-quality noise")
        print(f"Marked {marked} posts in Neo4j")
    else:
        print("No crap posts identified")
