"""Master crawler orchestration."""

import time
from typing import List, Optional, Dict
from datetime import datetime
import numpy as np

from .frontier import CrawlFrontier
from .fetch_worker import FetchWorker
from .storage import ImageStorage
from .vector_store import VectorStore
from .deduplication import ImageDeduplicator
from .quality_scorer import QualityScorer
from .face_filter import FaceFilter
from .platforms.base import BasePlatformCrawler
from ..feed.storage.neo4j_connection import Neo4jConnection
from ..feed.storage.valkey_connection import ValkeyConnection


class MasterCrawler:
    """Orchestrates the complete image crawling pipeline."""

    def __init__(
        self,
        neo4j: Optional[Neo4jConnection] = None,
        valkey: Optional[ValkeyConnection] = None,
        target_face_embedding: Optional[np.ndarray] = None,
        face_similarity_threshold: float = 0.65,
        num_workers: int = 1,
    ):
        """
        Initialize master crawler.

        Args:
            neo4j: Neo4j connection (creates if None)
            valkey: Valkey connection (creates if None)
            target_face_embedding: Optional target face embedding for filtering
            face_similarity_threshold: Face similarity threshold
            num_workers: Number of fetch workers
        """
        if neo4j is None:
            from ..feed.storage.neo4j_connection import get_connection
            neo4j = get_connection()

        if valkey is None:
            from ..feed.storage.valkey_connection import get_valkey_connection
            valkey = get_valkey_connection()

        self.neo4j = neo4j
        self.valkey = valkey

        self.storage = ImageStorage(neo4j)
        self.vector_store = VectorStore(valkey)
        self.frontier = CrawlFrontier(valkey)
        self.deduplicator = ImageDeduplicator(
            self.storage,
            self.vector_store,
            valkey
        )
        self.quality_scorer = QualityScorer()

        self.face_filter = None
        if target_face_embedding is not None:
            self.face_filter = FaceFilter(
                target_face_embedding=target_face_embedding,
                similarity_threshold=face_similarity_threshold,
            )

        self.workers = [
            FetchWorker(
                storage=self.storage,
                vector_store=self.vector_store,
                deduplicator=self.deduplicator,
                quality_scorer=self.quality_scorer,
                face_filter=self.face_filter,
            )
            for _ in range(num_workers)
        ]

        self.platform_crawlers: List[BasePlatformCrawler] = []

    def add_platform_crawler(self, crawler: BasePlatformCrawler) -> None:
        """
        Add a platform crawler.

        Args:
            crawler: Platform crawler instance
        """
        self.platform_crawlers.append(crawler)

    def extract_linked_images(self, url: str) -> List[str]:
        """
        Extract image URLs from a web page using HTML parsing.
        
        Note: This is for general web pages (e.g., imgur, external links), NOT for
        Reddit posts. Reddit posts are handled via RedditAdapter using JSON API.

        Args:
            url: Web page URL

        Returns:
            List of image URLs found on page
        """
        try:
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            image_urls = []

            for img_tag in soup.find_all("img"):
                src = img_tag.get("src") or img_tag.get("data-src")
                if src:
                    if src.startswith("//"):
                        src = "https:" + src
                    elif src.startswith("/"):
                        from urllib.parse import urljoin
                        src = urljoin(url, src)
                    image_urls.append(src)

            return image_urls
        except Exception:
            return []

    def run(self, max_urls: Optional[int] = None, max_duration: Optional[int] = None) -> None:
        """
        Run the crawler main loop.

        Args:
            max_urls: Maximum URLs to process (None = unlimited)
            max_duration: Maximum duration in seconds (None = unlimited)
        """
        start_time = datetime.utcnow()
        urls_processed = 0

        while True:
            if max_urls and urls_processed >= max_urls:
                break

            if max_duration:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= max_duration:
                    break

            for platform_crawler in self.platform_crawlers:
                if platform_crawler.should_check():
                    image_urls = platform_crawler.fetch_image_urls(limit=50)
                    for url in image_urls:
                        self.frontier.add_url(url, priority=10)

            url = self.frontier.pop_url()

            if not url:
                time.sleep(1)
                continue

            worker = self.workers[urls_processed % len(self.workers)]
            result = worker.process_url(url)

            if result:
                urls_processed += 1

                if not result.get("is_duplicate"):
                    new_urls = self.extract_linked_images(url)
                    for new_url in new_urls:
                        self.frontier.add_url(new_url, priority=3)

            time.sleep(0.1)

    def get_stats(self) -> Dict:
        """
        Get crawler statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "queue_size": self.frontier.get_queue_size(),
            "bloom_capacity": self.frontier.bloom_capacity,
        }

