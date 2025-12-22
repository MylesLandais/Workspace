#!/usr/bin/env python3
"""
IMDB Matcher Module

Provides functionality to search IMDB and fetch metadata for movies and TV shows.
Uses the cinemagoer library to access IMDB data.
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

try:
    from imdb import Cinemagoer
except ImportError:
    Cinemagoer = None

logger = logging.getLogger(__name__)


@dataclass
class IMDBResult:
    """Result from IMDB search."""
    imdb_id: str  # e.g., "tt0898897"
    title: str
    year: Optional[int]
    type: str  # "movie" or "tv series"
    plot: Optional[str] = None
    rating: Optional[float] = None


class IMDBMatcher:
    """Handles IMDB search and metadata retrieval."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize IMDB matcher.
        
        Args:
            cache_dir: Optional directory for caching IMDB lookups
        """
        if Cinemagoer is None:
            raise ImportError(
                "cinemagoer (imdb) package is required. "
                "Install with: pip install cinemagoer"
            )
        
        self.ia = Cinemagoer()
        self.cache_dir = cache_dir
        self._cache: Dict[str, Optional[IMDBResult]] = {}
        
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"IMDB cache directory: {cache_dir}")
    
    def search_imdb(
        self,
        title: str,
        year: Optional[int] = None
    ) -> Optional[IMDBResult]:
        """
        Search IMDB for a movie/TV show by title and optional year.
        
        Args:
            title: Movie/TV show title
            year: Release year (optional, helps with disambiguation)
            
        Returns:
            IMDBResult if match found, None otherwise
        """
        # Normalize title for cache key
        cache_key = f"{title.lower().strip()}:{year or 'none'}"
        
        # Check cache first
        if cache_key in self._cache:
            logger.debug(f"Cache hit for: {title} ({year})")
            return self._cache[cache_key]
        
        try:
            logger.info(f"Searching IMDB for: {title}" + (f" ({year})" if year else ""))
            
            # Search IMDB
            movies = self.ia.search_movie(title)
            
            if not movies:
                logger.warning(f"No IMDB results found for: {title}")
                self._cache[cache_key] = None
                return None
            
            # Try to find best match
            best_match = None
            best_score = 0
            
            for movie in movies[:10]:  # Check top 10 results
                score = self._calculate_match_score(movie, title, year)
                if score > best_score:
                    best_score = score
                    best_match = movie
            
            if best_match is None or best_score < 0.5:
                logger.warning(f"No good IMDB match found for: {title}")
                self._cache[cache_key] = None
                return None
            
            # Fetch full movie details
            self.ia.update(best_match, ['main'])
            
            # Extract IMDB ID
            imdb_id = best_match.movieID
            if not imdb_id.startswith('tt'):
                imdb_id = f"tt{imdb_id}"
            
            # Extract year
            result_year = best_match.get('year')
            
            # Extract title
            result_title = best_match.get('title', title)
            
            # Determine type
            kind = best_match.get('kind', 'movie')
            if 'tv' in kind.lower() or 'series' in kind.lower():
                result_type = "tv series"
            else:
                result_type = "movie"
            
            # Extract additional metadata
            plot = best_match.get('plot', [None])[0] if best_match.get('plot') else None
            rating = best_match.get('rating')
            
            result = IMDBResult(
                imdb_id=imdb_id,
                title=result_title,
                year=result_year,
                type=result_type,
                plot=plot,
                rating=rating
            )
            
            logger.info(f"Found IMDB match: {result_title} ({result_year}) [{imdb_id}]")
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error searching IMDB for {title}: {e}", exc_info=True)
            self._cache[cache_key] = None
            return None
    
    def _calculate_match_score(
        self,
        movie: Any,
        search_title: str,
        search_year: Optional[int]
    ) -> float:
        """
        Calculate match score between search query and IMDB result.
        
        Args:
            movie: IMDB movie object
            search_title: Search title
            search_year: Search year (optional)
            
        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        
        # Normalize titles for comparison
        movie_title = movie.get('title', '').lower().strip()
        search_title_norm = search_title.lower().strip()
        
        # Exact title match gets high score
        if movie_title == search_title_norm:
            score += 0.7
        elif movie_title.startswith(search_title_norm) or search_title_norm.startswith(movie_title):
            score += 0.5
        else:
            # Partial match (check if key words match)
            search_words = set(search_title_norm.split())
            movie_words = set(movie_title.split())
            common_words = search_words & movie_words
            if common_words:
                score += 0.3 * (len(common_words) / max(len(search_words), len(movie_words)))
        
        # Year match boosts score
        movie_year = movie.get('year')
        if search_year and movie_year:
            if movie_year == search_year:
                score += 0.3
            elif abs(movie_year - search_year) <= 1:
                score += 0.1
        
        return min(score, 1.0)
    
    def get_imdb_by_id(self, imdb_id: str) -> Optional[IMDBResult]:
        """
        Get IMDB metadata by IMDB ID directly.
        
        Args:
            imdb_id: IMDB ID (e.g., "tt0898897" or "0898897")
            
        Returns:
            IMDBResult if found, None otherwise
        """
        # Normalize IMDB ID
        imdb_id = imdb_id.strip().lower()
        if not imdb_id.startswith('tt'):
            imdb_id = f"tt{imdb_id}"
        
        cache_key = f"id:{imdb_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            logger.info(f"Fetching IMDB data for ID: {imdb_id}")
            
            # Get movie by ID
            movie = self.ia.get_movie(imdb_id.replace('tt', ''))
            self.ia.update(movie, ['main'])
            
            # Extract metadata
            result_title = movie.get('title', '')
            result_year = movie.get('year')
            kind = movie.get('kind', 'movie')
            
            if 'tv' in kind.lower() or 'series' in kind.lower():
                result_type = "tv series"
            else:
                result_type = "movie"
            
            plot = movie.get('plot', [None])[0] if movie.get('plot') else None
            rating = movie.get('rating')
            
            result = IMDBResult(
                imdb_id=imdb_id,
                title=result_title,
                year=result_year,
                type=result_type,
                plot=plot,
                rating=rating
            )
            
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error fetching IMDB data for {imdb_id}: {e}", exc_info=True)
            self._cache[cache_key] = None
            return None


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    matcher = IMDBMatcher()
    
    # Test search
    result = matcher.search_imdb("Ballerina", 2006)
    if result:
        print(f"Found: {result.title} ({result.year}) [{result.imdb_id}]")
        print(f"Type: {result.type}")
        if result.rating:
            print(f"Rating: {result.rating}")
    else:
        print("No match found")

