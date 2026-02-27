"""URL Frontier with bloom filter and priority queue."""

import hashlib
from typing import Optional, List, Dict
from urllib.parse import urlparse, urlunparse, parse_qs
import redis
from pybloom_live import BloomFilter

from ..feed.storage.valkey_connection import ValkeyConnection


class URLNormalizer:
    """Normalizes URLs for duplicate detection."""

    @staticmethod
    def normalize(url: str) -> str:
        """
        Normalize URL to canonical form.

        Args:
            url: Original URL string

        Returns:
            Normalized URL string
        """
        if not url:
            return ""

        parsed = urlparse(url.strip())

        scheme = parsed.scheme.lower() or "http"
        if scheme not in ["http", "https"]:
            return url

        netloc = parsed.netloc.lower()
        if scheme == "http" and netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif scheme == "https" and netloc.endswith(":443"):
            netloc = netloc[:-4]

        path = parsed.path.rstrip("/") or "/"

        query_params = parse_qs(parsed.query, keep_blank_values=True)
        tracking_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term",
            "utm_content", "fbclid", "gclid", "_ga", "ref", "v", "t"
        }
        filtered_params = {
            k: v for k, v in query_params.items()
            if k.lower() not in tracking_params
        }

        if filtered_params:
            sorted_params = sorted(filtered_params.items())
            query = "&".join(
                f"{k}={v[0]}" if len(v) == 1 else f"{k}={','.join(sorted(v))}"
                for k, v in sorted_params
            )
        else:
            query = ""

        normalized = urlunparse((scheme, netloc, path, parsed.params, query, ""))
        return normalized

    @staticmethod
    def extract_domain(url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: URL string

        Returns:
            Domain string
        """
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            return netloc
        except Exception:
            return ""


class CrawlFrontier:
    """Manages URL crawl queue with bloom filter and priority queue."""

    BLOOM_KEY = "crawl:bloom"
    QUEUE_KEY = "crawl:queue"
    BLOOM_CAPACITY = 10_000_000
    BLOOM_ERROR_RATE = 0.001

    def __init__(
        self,
        valkey: ValkeyConnection,
        bloom_capacity: int = BLOOM_CAPACITY,
        bloom_error_rate: float = BLOOM_ERROR_RATE,
    ):
        """
        Initialize crawl frontier.

        Args:
            valkey: Valkey connection instance
            bloom_capacity: Bloom filter capacity
            bloom_error_rate: Bloom filter false positive rate
        """
        self.valkey = valkey
        self.client = valkey.client
        self.normalizer = URLNormalizer()
        self.bloom_capacity = bloom_capacity
        self.bloom_error_rate = bloom_error_rate
        self._bloom: Optional[BloomFilter] = None

    def _get_bloom(self) -> BloomFilter:
        """Get or create bloom filter."""
        if self._bloom is None:
            bloom_data = self.client.get(self.BLOOM_KEY)
            if bloom_data:
                self._bloom = BloomFilter.from_base64(bloom_data.decode())
            else:
                self._bloom = BloomFilter(
                    capacity=self.bloom_capacity,
                    error_rate=self.bloom_error_rate
                )
        return self._bloom

    def _save_bloom(self) -> None:
        """Save bloom filter to Valkey."""
        if self._bloom:
            bloom_data = self._bloom.to_base64()
            self.client.set(self.BLOOM_KEY, bloom_data)

    def add_url(self, url: str, priority: float = 0.0) -> bool:
        """
        Add URL to frontier if not already present.

        Args:
            url: URL to add
            priority: Priority score (higher = more important)

        Returns:
            True if URL was added, False if already exists
        """
        canonical = self.normalizer.normalize(url)
        if not canonical:
            return False

        bloom = self._get_bloom()

        if canonical in bloom:
            return False

        bloom.add(canonical)
        self._save_bloom()

        self.client.zadd(self.QUEUE_KEY, {canonical: priority})
        return True

    def pop_url(self) -> Optional[str]:
        """
        Get and remove highest priority URL from queue.

        Returns:
            URL or None if queue is empty
        """
        result = self.client.zpopmax(self.QUEUE_KEY, count=1)
        if result:
            return result[0][0].decode()
        return None

    def get_next_urls(self, limit: int = 10) -> List[str]:
        """
        Get next URLs from queue without removing them.

        Args:
            limit: Maximum number of URLs to return

        Returns:
            List of URLs ordered by priority (highest first)
        """
        results = self.client.zrevrange(self.QUEUE_KEY, 0, limit - 1)
        return [url.decode() for url in results]

    def remove_url(self, url: str) -> None:
        """
        Remove URL from queue.

        Args:
            url: URL to remove
        """
        canonical = self.normalizer.normalize(url)
        self.client.zrem(self.QUEUE_KEY, canonical)

    def get_queue_size(self) -> int:
        """
        Get current queue size.

        Returns:
            Number of URLs in queue
        """
        return self.client.zcard(self.QUEUE_KEY)

    def has_url(self, url: str) -> bool:
        """
        Check if URL is in bloom filter (has been seen).

        Args:
            url: URL to check

        Returns:
            True if URL has been seen
        """
        canonical = self.normalizer.normalize(url)
        bloom = self._get_bloom()
        return canonical in bloom

    def get_url_hash(self, url: str) -> str:
        """
        Get hash of normalized URL for indexing.

        Args:
            url: URL string

        Returns:
            MD5 hash of normalized URL
        """
        canonical = self.normalizer.normalize(url)
        return hashlib.md5(canonical.encode()).hexdigest()








