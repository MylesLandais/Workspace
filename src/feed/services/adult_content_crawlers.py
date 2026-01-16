"""Multi-source crawlers for adult content databases.

Supports:
- Data18.com
- IAFD.com (Internet Adult Film Database)
- Indexxx.com
- Adult-specific reverse image search tools
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime


@dataclass
class Performer:
    """Performer/actor information."""
    name: str
    performer_id: str
    profile_url: str
    source: str  # 'data18', 'iafd', 'indexxx'
    fantasyhd_scenes: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Scene:
    """Scene information."""
    scene_id: str
    title: str
    studio: str
    performers: List[str]
    release_date: Optional[str] = None
    url: str = ""
    description: Optional[str] = None
    source: str = ""  # 'data18', 'iafd', 'indexxx'


class Data18Crawler:
    """Enhanced Data18.com crawler."""
    
    BASE_URL = "https://www.data18.com"
    
    def __init__(self, delay_min: float = 2.0, delay_max: float = 5.0):
        """Initialize Data18 crawler with rate limiting."""
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def _delay(self):
        """Random delay between requests."""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def get_studio_performers(self, studio_slug: str) -> List[Performer]:
        """
        Get all performers for a studio.
        
        Args:
            studio_slug: Studio slug (e.g., 'fantasyhd')
            
        Returns:
            List of Performer objects
        """
        url = f"{self.BASE_URL}/studios/{studio_slug}/pornstars"
        self._delay()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            performers = []
            
            # Parse performer list - adjust selectors based on actual HTML
            performer_elements = soup.find_all('a', href=re.compile(r'/pornstars/'))
            
            seen_ids = set()
            for element in performer_elements:
                name = element.get_text(strip=True)
                href = element.get('href', '')
                performer_id = href.split('/')[-1] if href else None
                
                if name and performer_id and performer_id not in seen_ids:
                    seen_ids.add(performer_id)
                    performers.append(Performer(
                        name=name,
                        performer_id=performer_id,
                        profile_url=f"{self.BASE_URL}{href}" if href.startswith('/') else href,
                        source='data18'
                    ))
            
            return performers
        except Exception as e:
            print(f"Error fetching studio performers from Data18: {e}")
            return []
    
    def get_performer_fantasyhd_scenes(
        self,
        performer_id: str,
        studio_slug: str = "fantasyhd"
    ) -> List[Scene]:
        """
        Get FantasyHD scenes for a specific performer.
        
        Args:
            performer_id: Performer ID
            studio_slug: Studio slug
            
        Returns:
            List of Scene objects
        """
        url = f"{self.BASE_URL}/pornstars/{performer_id}/scenes"
        self._delay()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            scenes = []
            
            # Filter for FantasyHD scenes
            scene_elements = soup.find_all('div', class_=re.compile(r'scene|video'))
            
            for element in scene_elements:
                # Check if scene is from FantasyHD
                studio_link = element.find('a', href=re.compile(f'/studios/{studio_slug}'))
                if not studio_link:
                    continue
                
                title_elem = element.find('a', href=re.compile(r'/scenes/'))
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    scene_id = href.split('/')[-1] if href else None
                    
                    if title and scene_id:
                        scenes.append(Scene(
                            scene_id=scene_id,
                            title=title,
                            studio=studio_slug,
                            performers=[],  # Would extract from element
                            url=f"{self.BASE_URL}{href}" if href.startswith('/') else href,
                            source='data18'
                        ))
            
            return scenes
        except Exception as e:
            print(f"Error fetching performer scenes from Data18: {e}")
            return []
    
    def search_scenes_by_studio(
        self,
        studio_slug: str,
        keywords: Optional[List[str]] = None
    ) -> List[Scene]:
        """Search scenes for a studio with optional keywords."""
        # Get all performers
        performers = self.get_studio_performers(studio_slug)
        
        all_scenes = []
        for performer in performers[:20]:  # Limit for performance
            scenes = self.get_performer_fantasyhd_scenes(
                performer.performer_id,
                studio_slug
            )
            all_scenes.extend(scenes)
        
        # Filter by keywords if provided
        if keywords:
            filtered = []
            for scene in all_scenes:
                title_lower = scene.title.lower()
                if any(kw.lower() in title_lower for kw in keywords):
                    filtered.append(scene)
            return filtered
        
        return all_scenes


class IAFDCrawler:
    """IAFD.com (Internet Adult Film Database) crawler."""
    
    BASE_URL = "https://www.iafd.com"
    
    def __init__(self, delay_min: float = 2.0, delay_max: float = 5.0):
        """Initialize IAFD crawler."""
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def _delay(self):
        """Random delay between requests."""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def get_distributor_titles(
        self,
        distributor: str = "fantasyhd.com"
    ) -> List[Scene]:
        """
        Get all titles for a distributor.
        
        Args:
            distributor: Distributor name (e.g., 'fantasyhd.com')
            
        Returns:
            List of Scene objects
        """
        # IAFD distributor page format
        url = f"{self.BASE_URL}/distrib.rme/distrib=7411/{distributor}.htm"
        self._delay()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            scenes = []
            
            # Parse title list - adjust selectors based on actual HTML
            title_elements = soup.find_all('a', href=re.compile(r'/title/'))
            
            for element in title_elements:
                title = element.get_text(strip=True)
                href = element.get('href', '')
                scene_id = href.split('/')[-1].replace('.htm', '') if href else None
                
                if title and scene_id:
                    scenes.append(Scene(
                        scene_id=scene_id,
                        title=title,
                        studio=distributor,
                        performers=[],  # Would extract from page
                        url=f"{self.BASE_URL}{href}" if href.startswith('/') else href,
                        source='iafd'
                    ))
            
            return scenes
        except Exception as e:
            print(f"Error fetching distributor titles from IAFD: {e}")
            return []
    
    def get_performer_fantasyhd_titles(
        self,
        performer_name: str
    ) -> List[Scene]:
        """
        Get FantasyHD titles for a performer.
        
        Args:
            performer_name: Performer name
            
        Returns:
            List of Scene objects
        """
        # Search performer page
        search_url = f"{self.BASE_URL}/person.rme/perfid={performer_name.lower().replace(' ', '_')}"
        self._delay()
        
        try:
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            scenes = []
            
            # Find FantasyHD titles in performer filmography
            fantasyhd_section = soup.find('div', string=re.compile('FantasyHD', re.I))
            if fantasyhd_section:
                title_elements = fantasyhd_section.find_all_next('a', href=re.compile(r'/title/'), limit=50)
                
                for element in title_elements:
                    title = element.get_text(strip=True)
                    href = element.get('href', '')
                    scene_id = href.split('/')[-1].replace('.htm', '') if href else None
                    
                    if title and scene_id:
                        scenes.append(Scene(
                            scene_id=scene_id,
                            title=title,
                            studio='fantasyhd',
                            performers=[performer_name],
                            url=f"{self.BASE_URL}{href}" if href.startswith('/') else href,
                            source='iafd'
                        ))
            
            return scenes
        except Exception as e:
            print(f"Error fetching performer titles from IAFD: {e}")
            return []


class IndexxxCrawler:
    """Indexxx.com crawler."""
    
    BASE_URL = "https://www.indexxx.com"
    
    def __init__(self, delay_min: float = 2.0, delay_max: float = 5.0):
        """Initialize Indexxx crawler."""
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def _delay(self):
        """Random delay between requests."""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def get_model_fantasyhd_scenes(
        self,
        model_name: str
    ) -> List[Scene]:
        """
        Get FantasyHD scenes for a model.
        
        Args:
            model_name: Model name
            
        Returns:
            List of Scene objects with dates and co-stars
        """
        # Search model profile
        search_url = f"{self.BASE_URL}/models/{model_name.lower().replace(' ', '-')}"
        self._delay()
        
        try:
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            scenes = []
            
            # Find FantasyHD section in model profile
            fantasyhd_section = soup.find('div', string=re.compile('FantasyHD', re.I))
            if fantasyhd_section:
                scene_elements = fantasyhd_section.find_all_next('div', class_=re.compile(r'scene|video'))
                
                for element in scene_elements[:50]:  # Limit results
                    title_elem = element.find('a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        href = title_elem.get('href', '')
                        scene_id = href.split('/')[-1] if href else None
                        
                        # Extract date and co-stars from element
                        date_elem = element.find('span', class_=re.compile(r'date'))
                        date = date_elem.get_text(strip=True) if date_elem else None
                        
                        co_stars = []
                        co_star_links = element.find_all('a', href=re.compile(r'/models/'))
                        for link in co_star_links:
                            if link.get_text(strip=True) != title:
                                co_stars.append(link.get_text(strip=True))
                        
                        if title and scene_id:
                            scenes.append(Scene(
                                scene_id=scene_id,
                                title=title,
                                studio='fantasyhd',
                                performers=[model_name] + co_stars,
                                release_date=date,
                                url=f"{self.BASE_URL}{href}" if href.startswith('/') else href,
                                source='indexxx'
                            ))
            
            return scenes
        except Exception as e:
            print(f"Error fetching model scenes from Indexxx: {e}")
            return []


class AdultReverseImageSearch:
    """Adult-specific reverse image search integration."""
    
    def __init__(self):
        """Initialize adult reverse image search."""
        # Placeholder for adult-specific reverse image search APIs
        # Examples: NameThatPorn, PornMD, etc.
        pass
    
    def search_by_image(
        self,
        image_path: str,
        provider: str = "namethatporn"
    ) -> List[Dict[str, Any]]:
        """
        Search for adult content using reverse image search.
        
        Args:
            image_path: Path to image file
            provider: Search provider ('namethatporn', 'pornmd', etc.)
            
        Returns:
            List of search results with performer names, scene titles, etc.
        """
        # TODO: Implement actual API calls to adult reverse image search services
        # These typically require:
        # 1. Image upload or URL
        # 2. API key (if available)
        # 3. Parse results for performer/scene information
        
        results = []
        
        # Placeholder structure
        if provider == "namethatporn":
            # Example: https://namethatporn.com API
            pass
        elif provider == "pornmd":
            # Example: PornMD reverse search
            pass
        
        return results


class MultiSourceCrawler:
    """Orchestrates multiple database crawlers."""
    
    def __init__(
        self,
        delay_min: float = 2.0,
        delay_max: float = 5.0
    ):
        """Initialize multi-source crawler."""
        self.data18 = Data18Crawler(delay_min, delay_max)
        self.iafd = IAFDCrawler(delay_min, delay_max)
        self.indexxx = IndexxxCrawler(delay_min, delay_max)
        self.reverse_search = AdultReverseImageSearch()
    
    def get_all_fantasyhd_performers(self) -> List[Performer]:
        """
        Get FantasyHD performers from all sources.
        
        Returns:
            Deduplicated list of performers
        """
        all_performers = {}
        
        # Data18
        data18_performers = self.data18.get_studio_performers("fantasyhd")
        for p in data18_performers:
            key = p.name.lower()
            if key not in all_performers:
                all_performers[key] = p
        
        # IAFD and Indexxx would require different approaches
        # (they don't have direct studio performer lists)
        
        return list(all_performers.values())
    
    def search_scenes_multi_source(
        self,
        studio: str = "fantasyhd",
        performer_name: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> List[Scene]:
        """
        Search scenes across all sources.
        
        Args:
            studio: Studio name
            performer_name: Optional performer name to filter
            keywords: Optional keywords to filter
            
        Returns:
            Combined and deduplicated scene list
        """
        all_scenes = {}
        
        # Data18
        if performer_name:
            # Would need to find performer ID first
            pass
        else:
            data18_scenes = self.data18.search_scenes_by_studio(studio, keywords)
            for scene in data18_scenes:
                key = scene.title.lower()
                if key not in all_scenes:
                    all_scenes[key] = scene
        
        # IAFD
        iafd_scenes = self.iafd.get_distributor_titles("fantasyhd.com")
        for scene in iafd_scenes:
            key = scene.title.lower()
            if key not in all_scenes:
                all_scenes[key] = scene
        
        # Indexxx (requires performer name)
        if performer_name:
            indexxx_scenes = self.indexxx.get_model_fantasyhd_scenes(performer_name)
            for scene in indexxx_scenes:
                key = scene.title.lower()
                if key not in all_scenes:
                    all_scenes[key] = scene
        
        return list(all_scenes.values())
    
    def identify_performer_from_image(
        self,
        image_path: str
    ) -> List[Dict[str, Any]]:
        """
        Identify performer using adult reverse image search.
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of potential matches with confidence scores
        """
        results = self.reverse_search.search_by_image(image_path)
        return results




