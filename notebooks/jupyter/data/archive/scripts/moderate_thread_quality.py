"""Moderation service for identifying and marking low-quality/bot posts."""

from typing import List, Dict, Any, Optional
import re
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from feed.storage.neo4j_connection import get_connection
from feed.services.post_moderation import PostModerationService, ModerationReason


class LowQualityDetector:
    """Detect low-quality and bot-like posts."""
    
    def __init__(self):
        # Hex pattern (long random-looking strings)
        self.hex_pattern = re.compile(r'[0-9a-f]{16,}')
        
        # Bot/spam patterns
        self.spam_patterns = [
            r'nut after nut after nut after',  # Repetitive nonsense
            r'\buh oh\b',  # Low effort
            r'^[a-f0-9]{32,}$',  # Long hex strings
        ]
        
        # Short low-effort posts
        self.low_effort_patterns = [
            r'^based,? ngl$',  # Very short, low value
            r'^wow$',  # Very short
            r'^uh oh$',  # Very short
        ]
    
    def analyze_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a post and determine if it's low quality.
        
        Args:
            post: Post dictionary with 'text', 'no', etc.
            
        Returns:
            Dictionary with 'is_low_quality', 'reason', 'confidence' keys
        """
        text = post.get("comment", "").lower()
        post_no = post.get("no", "")
        
        # Skip posts with images (generally higher quality)
        if post.get("image_url"):
            return {
                "is_low_quality": False,
                "reason": "has_image",
                "confidence": 0.0
            }
        
        # Check for spam/bot patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "is_low_quality": True,
                    "reason": "bot_pattern",
                    "confidence": 0.85
                }
        
        # Check for hex/random strings
        if self.hex_pattern.search(text):
            return {
                "is_low_quality": True,
                "reason": "hex_random",
                "confidence": 0.90
            }
        
        # Check for very short low-effort posts
        for pattern in self.low_effort_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return {
                    "is_low_quality": True,
                    "reason": "low_effort",
                    "confidence": 0.60
                }
        
        # Check for extremely short posts (under 3 chars)
        if len(text.strip()) < 3:
            return {
                "is_low_quality": True,
                "reason": "very_short",
                "confidence": 0.50
            }
        
        return {
            "is_low_quality": False,
            "reason": None,
            "confidence": 0.0
        }
    
    def analyze_thread(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze all posts in a thread.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            List of analysis results for each post
        """
        results = []
        for post in posts:
            analysis = self.analyze_post(post)
            analysis["post_no"] = post.get("no", "")
            analysis["text_preview"] = post.get("comment", "")[:50]
            results.append(analysis)
        return results


def mark_crap_posts(
    board: str,
    thread_id: int,
    posts: List[Dict[str, Any]],
    flag: str = "tagged for bot and low-quality noise"
) -> Dict[str, int]:
    """
    Identify and mark low-quality posts in a thread.
    
    Args:
        board: Board name (e.g., "b")
        thread_id: Thread ID
        posts: List of posts to analyze
        flag: Flag label to apply
        
    Returns:
        Dictionary with counts of analyzed, hidden, errors
    """
    detector = LowQualityDetector()
    service = PostModerationService()
    
    stats = {
        "analyzed": len(posts),
        "hidden": 0,
        "errors": 0,
        "hidden_posts": []
    }
    
    for post in posts:
        try:
            analysis = detector.analyze_post(post)
            
            if analysis["is_low_quality"]:
                post_no = post.get("no")
                if not post_no:
                    continue
                
                post_id = f"{board}_{thread_id}_{post_no}"
                reason = f"low_quality: {analysis['reason']}"
                
                if service.hide_post(post_id, reason, flag):
                    stats["hidden"] += 1
                    stats["hidden_posts"].append({
                        "post_no": post_no,
                        "reason": analysis["reason"],
                        "confidence": analysis["confidence"]
                    })
        except Exception as e:
            stats["errors"] += 1
            print(f"Error processing post: {e}")
    
    return stats


if __name__ == "__main__":
    # Example usage for the thread from the request
    board = "b"
    thread_id = 944358701
    
    print(f"Analyzing thread /{board}/{thread_id}...")
    
    # In real usage, fetch from Neo4j:
    # For demo, use placeholder posts
    example_posts = [
        {"no": "944359013", "comment": "Nut after nut after nut after"},
        {"no": "944359826", "comment": "based, ngl"},
        {"no": "944359824", "comment": "05b3a2767b4bfe6f9e5171aa9"},
    ]
    
    results = mark_crap_posts(board, thread_id, example_posts)
    
    print(f"\nResults:")
    print(f"  Analyzed: {results['analyzed']}")
    print(f"  Hidden: {results['hidden']}")
    print(f"  Errors: {results['errors']}")
    
    if results["hidden_posts"]:
        print(f"\nHidden posts:")
        for hp in results["hidden_posts"]:
            print(f"  Post {hp['post_no']}: {hp['reason']} (confidence: {hp['confidence']})")
