"""Stash (stashapp/stash) integration for adult media identification.

Stash is a self-hosted adult media organizer with:
- Perceptual hashing for scene identification
- StashDB integration (crowd-sourced metadata)
- Community scrapers for FantasyHD and other studios
- Performer recognition and tagging
- Scene matching and metadata enrichment
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import requests
from datetime import datetime
import json


@dataclass
class StashPerformer:
    """Stash performer information."""
    id: str
    name: str
    url: Optional[str] = None
    stash_id: Optional[str] = None
    image_url: Optional[str] = None
    scene_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StashScene:
    """Stash scene information."""
    id: str
    title: str
    url: str
    date: Optional[str] = None
    studio: Optional[str] = None
    performers: List[StashPerformer] = None
    tags: List[str] = None
    stash_id: Optional[str] = None
    phash: Optional[str] = None  # Perceptual hash for matching
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StashMatch:
    """Stash scene/performer match result."""
    match_type: str  # 'phash', 'performer', 'title', 'stashdb'
    confidence: float
    scene: Optional[StashScene] = None
    performer: Optional[StashPerformer] = None
    stashdb_id: Optional[str] = None


class StashClient:
    """Client for Stash API (self-hosted instance)."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:9999",
        api_key: Optional[str] = None
    ):
        """
        Initialize Stash client.
        
        Args:
            base_url: Stash instance URL (e.g., "http://192.168.0.222:9999")
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                'ApiKey': api_key
            })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make API request to Stash.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body
            
        Returns:
            Response JSON
        """
        url = f"{self.base_url}/graphql" if endpoint.startswith('/') else f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=15)
            else:
                response = self.session.post(
                    url,
                    params=params,
                    json=json_data,
                    timeout=15
                )
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Stash API error: {e}")
            return {}
    
    def search_scenes(
        self,
        query: Optional[str] = None,
        performer_name: Optional[str] = None,
        studio: Optional[str] = None,
        limit: int = 50
    ) -> List[StashScene]:
        """
        Search scenes in Stash.
        
        Args:
            query: Text search query
            performer_name: Filter by performer name
            studio: Filter by studio
            limit: Maximum results
            
        Returns:
            List of StashScene objects
        """
        # Stash GraphQL query
        graphql_query = """
        query SearchScenes($filter: SceneFilterType) {
          findScenes(filter: $filter) {
            scenes {
              id
              title
              date
              url
              stash_ids {
                endpoint
                stash_id
              }
              phash
              studio {
                name
              }
              performers {
                id
                name
                stash_ids {
                  endpoint
                  stash_id
                }
              }
              tags {
                name
              }
            }
          }
        }
        """
        
        # Build filter
        filter_obj = {}
        if query:
            filter_obj["q"] = query
        if performer_name:
            filter_obj["performers"] = {"value": [performer_name], "modifier": "INCLUDES"}
        if studio:
            filter_obj["studios"] = {"value": [studio], "modifier": "INCLUDES"}
        
        variables = {
            "filter": filter_obj
        }
        
        response = self._request(
            'POST',
            '/graphql',
            json_data={
                "query": graphql_query,
                "variables": variables
            }
        )
        
        scenes = []
        if 'data' in response and 'findScenes' in response['data']:
            for scene_data in response['data']['findScenes'].get('scenes', [])[:limit]:
                performers = []
                for p in scene_data.get('performers', []):
                    performers.append(StashPerformer(
                        id=p.get('id', ''),
                        name=p.get('name', ''),
                        stash_id=p.get('stash_ids', [{}])[0].get('stash_id') if p.get('stash_ids') else None
                    ))
                
                scenes.append(StashScene(
                    id=scene_data.get('id', ''),
                    title=scene_data.get('title', ''),
                    url=scene_data.get('url', ''),
                    date=scene_data.get('date'),
                    studio=scene_data.get('studio', {}).get('name') if scene_data.get('studio') else None,
                    performers=performers,
                    tags=[t.get('name') for t in scene_data.get('tags', [])],
                    stash_id=scene_data.get('stash_ids', [{}])[0].get('stash_id') if scene_data.get('stash_ids') else None,
                    phash=scene_data.get('phash')
                ))
        
        return scenes
    
    def get_scene_by_id(self, scene_id: str) -> Optional[StashScene]:
        """
        Get scene by ID.
        
        Args:
            scene_id: Stash scene ID
            
        Returns:
            StashScene or None
        """
        graphql_query = """
        query GetScene($id: ID!) {
          findScene(id: $id) {
            id
            title
            date
            url
            stash_ids {
              endpoint
              stash_id
            }
            phash
            studio {
              name
            }
            performers {
              id
              name
              stash_ids {
                endpoint
                stash_id
              }
            }
            tags {
              name
            }
          }
        }
        """
        
        response = self._request(
            'POST',
            '/graphql',
            json_data={
                "query": graphql_query,
                "variables": {"id": scene_id}
            }
        )
        
        if 'data' in response and 'findScene' in response['data']:
            scene_data = response['data']['findScene']
            if scene_data:
                performers = []
                for p in scene_data.get('performers', []):
                    performers.append(StashPerformer(
                        id=p.get('id', ''),
                        name=p.get('name', ''),
                        stash_id=p.get('stash_ids', [{}])[0].get('stash_id') if p.get('stash_ids') else None
                    ))
                
                return StashScene(
                    id=scene_data.get('id', ''),
                    title=scene_data.get('title', ''),
                    url=scene_data.get('url', ''),
                    date=scene_data.get('date'),
                    studio=scene_data.get('studio', {}).get('name') if scene_data.get('studio') else None,
                    performers=performers,
                    tags=[t.get('name') for t in scene_data.get('tags', [])],
                    stash_id=scene_data.get('stash_ids', [{}])[0].get('stash_id') if scene_data.get('stash_ids') else None,
                    phash=scene_data.get('phash')
                )
        
        return None
    
    def search_performers(
        self,
        query: Optional[str] = None,
        limit: int = 50
    ) -> List[StashPerformer]:
        """
        Search performers in Stash.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of StashPerformer objects
        """
        graphql_query = """
        query SearchPerformers($filter: PerformerFilterType) {
          findPerformers(filter: $filter) {
            performers {
              id
              name
              url
              stash_ids {
                endpoint
                stash_id
              }
              image_path
              scene_count
            }
          }
        }
        """
        
        filter_obj = {}
        if query:
            filter_obj["q"] = query
        
        response = self._request(
            'POST',
            '/graphql',
            json_data={
                "query": graphql_query,
                "variables": {"filter": filter_obj}
            }
        )
        
        performers = []
        if 'data' in response and 'findPerformers' in response['data']:
            for p_data in response['data']['findPerformers'].get('performers', [])[:limit]:
                performers.append(StashPerformer(
                    id=p_data.get('id', ''),
                    name=p_data.get('name', ''),
                    url=p_data.get('url'),
                    stash_id=p_data.get('stash_ids', [{}])[0].get('stash_id') if p_data.get('stash_ids') else None,
                    scene_count=p_data.get('scene_count')
                ))
        
        return performers
    
    def match_scene_by_phash(
        self,
        phash: str,
        distance: int = 4
    ) -> List[StashMatch]:
        """
        Match scene using perceptual hash.
        
        Args:
            phash: Perceptual hash value
            distance: Maximum Hamming distance for match
            
        Returns:
            List of matching scenes
        """
        # Stash supports phash matching via GraphQL
        graphql_query = """
        query MatchByPhash($phash: String!) {
          findScenes(filter: { phash: $phash }) {
            scenes {
              id
              title
              phash
              stash_ids {
                stash_id
              }
            }
          }
        }
        """
        
        response = self._request(
            'POST',
            '/graphql',
            json_data={
                "query": graphql_query,
                "variables": {"phash": phash}
            }
        )
        
        matches = []
        if 'data' in response and 'findScenes' in response['data']:
            for scene_data in response['data']['findScenes'].get('scenes', []):
                scene = self.get_scene_by_id(scene_data.get('id'))
                if scene:
                    # Calculate Hamming distance for confidence
                    scene_phash = scene.phash
                    if scene_phash:
                        hamming = self._hamming_distance(phash, scene_phash)
                        confidence = 1.0 - (hamming / 64.0)  # Normalize to 0-1
                        
                        matches.append(StashMatch(
                            match_type='phash',
                            confidence=max(0.0, confidence),
                            scene=scene
                        ))
        
        return matches
    
    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate Hamming distance between two hashes."""
        if len(hash1) != len(hash2):
            return 64  # Max distance
        
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    
    def get_fantasyhd_scenes(
        self,
        limit: int = 100
    ) -> List[StashScene]:
        """
        Get all FantasyHD scenes from Stash.
        
        Args:
            limit: Maximum results
            
        Returns:
            List of FantasyHD scenes
        """
        return self.search_scenes(studio="FantasyHD", limit=limit)
    
    def get_fantasyhd_performers(self) -> List[StashPerformer]:
        """
        Get all FantasyHD performers from Stash.
        
        Returns:
            List of performers who appear in FantasyHD scenes
        """
        # Get FantasyHD scenes and extract unique performers
        scenes = self.get_fantasyhd_scenes(limit=500)
        
        performer_ids = set()
        for scene in scenes:
            for performer in scene.performers or []:
                performer_ids.add(performer.id)
        
        # Fetch full performer details
        performers = []
        for performer_id in list(performer_ids)[:200]:  # Limit for performance
            # Would need individual performer query
            pass
        
        return performers


class StashIntegration:
    """Integration service for Stash-based identification."""
    
    def __init__(
        self,
        stash_url: str = "http://localhost:9999",
        api_key: Optional[str] = None
    ):
        """
        Initialize Stash integration.
        
        Args:
            stash_url: Stash instance URL
            api_key: Optional API key
        """
        self.client = StashClient(stash_url, api_key)
    
    def identify_video_from_stash(
        self,
        video_path: str,
        compute_phash: bool = True
    ) -> List[StashMatch]:
        """
        Identify video using Stash perceptual hashing.
        
        Args:
            video_path: Path to video file
            compute_phash: Compute perceptual hash for matching
            
        Returns:
            List of StashMatch results
        """
        matches = []
        
        if compute_phash:
            # Compute phash from video
            phash = self._compute_video_phash(video_path)
            if phash:
                # Match against Stash
                phash_matches = self.client.match_scene_by_phash(phash)
                matches.extend(phash_matches)
        
        return matches
    
    def _compute_video_phash(self, video_path: str) -> Optional[str]:
        """
        Compute perceptual hash for video.
        
        Uses same algorithm as Stash (pHash).
        
        Args:
            video_path: Path to video file
            
        Returns:
            Perceptual hash string or None
        """
        # TODO: Implement phash computation
        # Stash uses pHash library for perceptual hashing
        # Would need to extract frame and compute hash
        return None
    
    def search_by_performer_name(
        self,
        performer_name: str,
        studio: Optional[str] = "FantasyHD"
    ) -> List[StashScene]:
        """
        Search scenes by performer name.
        
        Args:
            performer_name: Performer name
            studio: Optional studio filter
            
        Returns:
            List of matching scenes
        """
        return self.client.search_scenes(
            performer_name=performer_name,
            studio=studio
        )
    
    def get_stashdb_matches(
        self,
        scene_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get StashDB metadata for a scene.
        
        Args:
            scene_id: Stash scene ID
            
        Returns:
            StashDB metadata or None
        """
        scene = self.client.get_scene_by_id(scene_id)
        if scene and scene.stash_id:
            # StashDB lookup would go here
            # StashDB API endpoint: https://stashdb.org/api/v1/scenes/{stash_id}
            pass
        
        return None




