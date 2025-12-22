"""Unit tests for crawler components."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from src.feed.crawler.frontier import URLNormalizer, URLFrontier
from src.feed.crawler.scheduler import AdaptiveScheduler, DecayInterval
from src.feed.crawler.content import ContentAnalyzer, Simhash
from src.feed.crawler.deduplication import DuplicateDetector
from src.feed.crawler.robots import RobotsParser


class TestURLNormalizer(unittest.TestCase):
    """Test URL normalization."""
    
    def setUp(self):
        self.normalizer = URLNormalizer()
    
    def test_normalize_basic(self):
        """Test basic URL normalization."""
        url = "https://example.com/path"
        normalized = self.normalizer.normalize(url)
        self.assertEqual(normalized, "https://example.com/path")
    
    def test_normalize_remove_tracking_params(self):
        """Test removal of tracking parameters."""
        url = "https://example.com/path?utm_source=test&id=123&utm_medium=email"
        normalized = self.normalizer.normalize(url)
        self.assertIn("id=123", normalized)
        self.assertNotIn("utm_source", normalized)
        self.assertNotIn("utm_medium", normalized)
    
    def test_normalize_lowercase(self):
        """Test lowercase normalization."""
        url = "HTTPS://EXAMPLE.COM/Path"
        normalized = self.normalizer.normalize(url)
        self.assertEqual(normalized, "https://example.com/path")
    
    def test_normalize_remove_default_ports(self):
        """Test removal of default ports."""
        url = "https://example.com:443/path"
        normalized = self.normalizer.normalize(url)
        self.assertNotIn(":443", normalized)
    
    def test_extract_domain(self):
        """Test domain extraction."""
        url = "https://subdomain.example.com:8080/path?query=1"
        domain = self.normalizer.extract_domain(url)
        self.assertEqual(domain, "subdomain.example.com")
    
    def test_is_valid_url(self):
        """Test URL validation."""
        self.assertTrue(self.normalizer.is_valid_url("https://example.com/path"))
        self.assertTrue(self.normalizer.is_valid_url("http://example.com"))
        self.assertFalse(self.normalizer.is_valid_url("not-a-url"))
        self.assertFalse(self.normalizer.is_valid_url("ftp://example.com"))


class TestAdaptiveScheduler(unittest.TestCase):
    """Test adaptive decay scheduler."""
    
    def setUp(self):
        self.neo4j = Mock()
        self.scheduler = AdaptiveScheduler(self.neo4j)
    
    def test_get_next_interval_first_crawl(self):
        """Test interval for first crawl."""
        interval = self.scheduler.get_next_interval(None, changed=False)
        self.assertEqual(interval, DecayInterval.HOUR_1.value)
    
    def test_get_next_interval_change_detected(self):
        """Test interval reset when change detected."""
        interval = self.scheduler.get_next_interval(7.0, changed=True)
        self.assertEqual(interval, DecayInterval.HOUR_1.value)
    
    def test_get_next_interval_no_change(self):
        """Test interval increase when no change."""
        current = DecayInterval.HOUR_1.value
        next_interval = self.scheduler.get_next_interval(current, changed=False)
        self.assertGreater(next_interval, current)
    
    def test_get_next_interval_max_cap(self):
        """Test maximum interval cap."""
        interval = self.scheduler.get_next_interval(3000.0, changed=False)
        self.assertLessEqual(interval, DecayInterval.YEAR_7.value)


class TestContentAnalyzer(unittest.TestCase):
    """Test content analysis and hashing."""
    
    def setUp(self):
        self.analyzer = ContentAnalyzer()
    
    def test_compute_content_hash(self):
        """Test content hash computation."""
        content1 = "Test content"
        content2 = "Test content"
        content3 = "Different content"
        
        hash1 = self.analyzer.compute_content_hash(content1)
        hash2 = self.analyzer.compute_content_hash(content2)
        hash3 = self.analyzer.compute_content_hash(content3)
        
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex length
    
    def test_compute_simhash(self):
        """Test simhash computation."""
        content = "This is a test document with some content"
        simhash = self.analyzer.compute_simhash(content)
        self.assertIsNotNone(simhash)
        self.assertIsInstance(simhash, int)
    
    def test_detect_change_exact_match(self):
        """Test change detection with exact match."""
        hash1 = "abc123"
        hash2 = "abc123"
        changed = self.analyzer.detect_change(hash1, hash2, None, None)
        self.assertFalse(changed)
    
    def test_detect_change_different_hash(self):
        """Test change detection with different hash."""
        hash1 = "abc123"
        hash2 = "def456"
        changed = self.analyzer.detect_change(hash1, hash2, None, None)
        self.assertTrue(changed)
    
    def test_detect_change_near_duplicate(self):
        """Test change detection with near-duplicate simhash."""
        simhash1 = 12345
        simhash2 = 12346  # Small difference
        distance = Simhash.hamming_distance(simhash1, simhash2)
        if distance <= 3:
            changed = self.analyzer.detect_change(None, None, simhash1, simhash2)
            self.assertFalse(changed)
    
    def test_jaccard_similarity(self):
        """Test Jaccard similarity calculation."""
        content1 = "The quick brown fox jumps over the lazy dog"
        content2 = "The quick brown fox jumps over the lazy dog"
        similarity = self.analyzer.jaccard_similarity(content1, content2)
        self.assertGreater(similarity, 0.9)
        
        content3 = "Completely different text here"
        similarity2 = self.analyzer.jaccard_similarity(content1, content3)
        self.assertLess(similarity2, 0.5)


class TestSimhash(unittest.TestCase):
    """Test Simhash implementation."""
    
    def setUp(self):
        self.simhash = Simhash(64)
    
    def test_compute_simhash(self):
        """Test simhash computation."""
        features = ["word1", "word2", "word3"]
        hash_value = self.simhash.compute(features)
        self.assertIsInstance(hash_value, int)
        self.assertGreaterEqual(hash_value, 0)
    
    def test_hamming_distance(self):
        """Test Hamming distance calculation."""
        hash1 = 0b10101010
        hash2 = 0b10101011  # 1 bit different
        distance = Simhash.hamming_distance(hash1, hash2)
        self.assertEqual(distance, 1)
        
        hash3 = 0b11111111  # All bits different
        distance2 = Simhash.hamming_distance(hash1, hash3)
        self.assertGreater(distance2, 1)


class TestDuplicateDetector(unittest.TestCase):
    """Test duplicate detection."""
    
    def setUp(self):
        self.neo4j = Mock()
        self.detector = DuplicateDetector(self.neo4j)
    
    def test_is_url_visited(self):
        """Test URL visited check."""
        self.neo4j.execute_read.return_value = [{"url": "https://example.com"}]
        visited = self.detector.is_url_visited("https://example.com")
        self.assertTrue(visited)
        
        self.neo4j.execute_read.return_value = []
        visited = self.detector.is_url_visited("https://new.com")
        self.assertFalse(visited)


class TestRobotsParser(unittest.TestCase):
    """Test robots.txt parser."""
    
    def setUp(self):
        self.neo4j = Mock()
        self.parser = RobotsParser(self.neo4j, user_agent="test-bot")
    
    def test_parse_robots_txt(self):
        """Test robots.txt parsing."""
        content = """
        User-agent: test-bot
        Disallow: /private/
        Allow: /public/
        Crawl-delay: 10
        """
        rules = self.parser.parse_robots_txt(content)
        self.assertIn("/private/", rules["disallowed"])
        self.assertIn("/public/", rules["allowed"])
        self.assertEqual(rules["crawl_delay"], 10.0)
    
    def test_matches_pattern(self):
        """Test pattern matching."""
        self.assertTrue(self.parser._matches_pattern("/private/page", "/private/"))
        self.assertTrue(self.parser._matches_pattern("/private/", "/private/"))
        self.assertFalse(self.parser._matches_pattern("/public/page", "/private/"))
        
        # Test wildcard
        self.assertTrue(self.parser._matches_pattern("/private/anything", "/private/*"))


if __name__ == "__main__":
    unittest.main()

