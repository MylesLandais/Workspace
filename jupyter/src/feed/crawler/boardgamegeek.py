"""BoardGameGeek crawler/fetcher module."""

import time
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime

class BoardGameGeekFetcher:
    """Fetcher for BoardGameGeek XML API 2."""
    
    BASE_URL = "https://boardgamegeek.com/xmlapi2"
    
    def __init__(self, delay: float = 2.0):
        """
        Initialize fetcher.
        
        Args:
            delay: Delay in seconds between requests to avoid rate limiting.
        """
        self.delay = delay
        self.last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BoardGameTracker/1.0 (Contact: admin@example.com) Python/requests"
        })
    
    def _wait_for_rate_limit(self):
        """Wait to respect rate limits."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()

    def get_thing(self, thing_id: Union[int, str], stats: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific thing (game).
        
        Args:
            thing_id: BGG ID of the item.
            stats: Whether to include statistics (ranking, rating).
            
        Returns:
            Dictionary with game details or None if failed.
        """
        self._wait_for_rate_limit()
        
        url = f"{self.BASE_URL}/thing"
        params = {
            "id": str(thing_id),
            "stats": "1" if stats else "0"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # BGG sometimes returns 200 with "Queued" message for large requests,
            # but for single things it should be immediate.
            if response.status_code == 202:
                print(f"BGG request queued. Retrying in 5s...")
                time.sleep(5)
                return self.get_thing(thing_id, stats)
                
            return self._parse_thing_xml(response.content)
            
        except Exception as e:
            print(f"Error fetching thing {thing_id}: {e}")
            return None

    def _parse_thing_xml(self, xml_content: bytes) -> Optional[Dict[str, Any]]:
        """Parse the XML response from BGG thing endpoint."""
        try:
            root = ET.fromstring(xml_content)
            item = root.find("item")
            
            if item is None:
                return None
                
            # Basic properties
            bgg_id_str = item.get("id")
            if not bgg_id_str:
                return None
                
            data = {
                "bgg_id": int(bgg_id_str),
                "type": item.get("type"),
                "thumbnail": self._get_text(item, "thumbnail"),
                "image": self._get_text(item, "image"),
                "description": self._get_text(item, "description"),
                "year_published": self._get_int(item, "yearpublished"),
                "min_players": self._get_int(item, "minplayers"),
                "max_players": self._get_int(item, "maxplayers"),
                "playing_time": self._get_int(item, "playingtime"),
                "min_playtime": self._get_int(item, "minplaytime"),
                "max_playtime": self._get_int(item, "maxplaytime"),
                "min_age": self._get_int(item, "minage"),
            }
            
            # Name (primary)
            name_elem = item.find("name[@type='primary']")
            data["name"] = name_elem.get("value") if name_elem is not None else "Unknown"
            
            # Links (Categories, Mechanics, Designers, etc.)
            links = []
            for link in item.findall("link"):
                links.append({
                    "type": link.get("type"),
                    "id": link.get("id"),
                    "value": link.get("value")
                })
            data["links"] = links
            
            # Statistics
            stats = item.find("statistics/ratings")
            if stats is not None:
                data["users_rated"] = self._get_float(stats, "usersrated")
                data["average_rating"] = self._get_float(stats, "average")
                data["bayes_average_rating"] = self._get_float(stats, "bayesaverage")
                data["average_weight"] = self._get_float(stats, "averageweight") # Complexity
            
            return data
            
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            return None

    def _get_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        elem = parent.find(tag)
        return elem.text if elem is not None else None

    def _get_int(self, parent: ET.Element, tag: str) -> Optional[int]:
        elem = parent.find(tag)
        if elem is None:
            return None
        value = elem.get("value")
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _get_float(self, parent: ET.Element, tag: str) -> Optional[float]:
        elem = parent.find(tag)
        if elem is None:
            return None
        value = elem.get("value")
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None
