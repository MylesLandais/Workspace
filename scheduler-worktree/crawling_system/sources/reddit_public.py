import requests
import time
from typing import Iterator, Dict, Any, Optional
from ..core.interfaces import DataSource

class RedditPublicJsonSource(DataSource):
    """
    Fetches data from Reddit's public JSON endpoints.
    No OAuth required, but subject to strict rate limits and IP blocking.
    """

    def __init__(self, user_agent: str = "ResearchCrawler/0.1"):
        self.user_agent = user_agent
        self.base_url = "https://www.reddit.com"

    def fetch_feed(self, target_name: str, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """
        Yields posts from a subreddit's new feed.
        
        Args:
            target_name: Subreddit name (without 'r/').
            limit: Soft limit on items to fetch.
        """
        after = None
        count = 0
        
        # Reddit JSON API returns max 100 items per request, max 1000 items depth usually.
        # We page through until we hit the limit or run out of data.
        while count < limit:
            url = f"{self.base_url}/r/{target_name}/new.json"
            params = {"limit": 100}
            if after:
                params["after"] = after
            
            headers = {"User-Agent": self.user_agent}
            
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 429:
                    print("Rate limit hit. Sleeping for 30s...")
                    time.sleep(30)
                    continue
                
                if response.status_code != 200:
                    print(f"Error fetching {url}: {response.status_code}")
                    break
                
                data = response.json()
                children = data.get("data", {}).get("children", [])
                
                if not children:
                    break
                
                for child in children:
                    item = child.get("data", {})
                    yield item
                    count += 1
                    if count >= limit:
                        return

                after = data.get("data", {}).get("after")
                if not after:
                    break
                
                # Politeness delay
                time.sleep(2)
                
            except Exception as e:
                print(f"Exception fetching reddit feed: {e}")
                break
