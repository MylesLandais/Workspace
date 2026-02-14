"""Content analysis and hashing for duplicate detection."""

import hashlib
import re
from typing import Optional, Set, List
from collections import Counter


class Simhash:
    """Simhash implementation for near-duplicate detection."""
    
    def __init__(self, hash_bits: int = 64):
        """
        Initialize Simhash.
        
        Args:
            hash_bits: Number of bits in hash (64 or 128)
        """
        self.hash_bits = hash_bits
        self.max_hash = (1 << hash_bits) - 1
    
    def compute(self, features: List[str]) -> int:
        """
        Compute simhash from feature list.
        
        Args:
            features: List of feature strings (e.g., tokens, shingles)
            
        Returns:
            Simhash value as integer
        """
        if not features:
            return 0
        
        # Create vector of hash_bits dimensions
        v = [0] * self.hash_bits
        
        # Hash each feature and update vector
        for feature in features:
            # Hash feature to get bit pattern
            h = self._hash_feature(feature)
            for i in range(self.hash_bits):
                if h & (1 << i):
                    v[i] += 1
                else:
                    v[i] -= 1
        
        # Generate fingerprint: bit i is 1 if v[i] > 0, else 0
        fingerprint = 0
        for i in range(self.hash_bits):
            if v[i] > 0:
                fingerprint |= (1 << i)
        
        return fingerprint
    
    def _hash_feature(self, feature: str) -> int:
        """Hash a feature string to integer."""
        # Use MD5 for 64-bit, SHA-256 for 128-bit
        if self.hash_bits == 64:
            h = hashlib.md5(feature.encode('utf-8')).digest()
            return int.from_bytes(h[:8], byteorder='big')
        else:
            h = hashlib.sha256(feature.encode('utf-8')).digest()
            return int.from_bytes(h[:16], byteorder='big')
    
    @staticmethod
    def hamming_distance(hash1: int, hash2: int) -> int:
        """
        Calculate Hamming distance between two simhashes.
        
        Args:
            hash1: First simhash
            hash2: Second simhash
            
        Returns:
            Hamming distance (number of differing bits)
        """
        return bin(hash1 ^ hash2).count('1')


class ContentAnalyzer:
    """Analyzes web content for hashing and duplicate detection."""
    
    def __init__(self, simhash_bits: int = 64):
        """
        Initialize content analyzer.
        
        Args:
            simhash_bits: Number of bits for simhash (64 or 128)
        """
        self.simhash = Simhash(simhash_bits)
    
    def compute_content_hash(self, content: str) -> str:
        """
        Compute SHA-256 hash of content for exact duplicate detection.
        
        Args:
            content: Content string
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def compute_simhash(self, content: str) -> Optional[int]:
        """
        Compute simhash for near-duplicate detection.
        
        Args:
            content: Content string
            
        Returns:
            Simhash integer, or None if content is empty
        """
        if not content:
            return None
        
        features = self._extract_features(content)
        if not features:
            return None
        
        return self.simhash.compute(features)
    
    def _extract_features(self, content: str, shingle_size: int = 3) -> List[str]:
        """
        Extract features from content (tokens and shingles).
        
        Args:
            content: Content string
            shingle_size: Size of shingles (n-grams)
            
        Returns:
            List of feature strings
        """
        # Normalize content
        content = content.lower()
        
        # Extract words (tokens)
        words = re.findall(r'\b\w+\b', content)
        
        # Create shingles (overlapping n-grams)
        shingles = []
        for i in range(len(words) - shingle_size + 1):
            shingle = ' '.join(words[i:i + shingle_size])
            shingles.append(shingle)
        
        # Combine tokens and shingles
        features = words + shingles
        
        return features
    
    def detect_change(
        self,
        old_hash: Optional[str],
        new_hash: Optional[str],
        old_simhash: Optional[int],
        new_simhash: Optional[int],
        threshold: int = 3
    ) -> bool:
        """
        Detect if content has changed.
        
        Args:
            old_hash: Previous content hash
            new_hash: New content hash
            old_simhash: Previous simhash
            new_simhash: New simhash
            threshold: Hamming distance threshold for near-duplicates
            
        Returns:
            True if content changed significantly
        """
        # Exact match check
        if old_hash and new_hash and old_hash == new_hash:
            return False
        
        # Near-duplicate check using simhash
        if old_simhash is not None and new_simhash is not None:
            distance = Simhash.hamming_distance(old_simhash, new_simhash)
            if distance <= threshold:
                return False  # Near-duplicate, no significant change
        
        # If we have hashes and they differ, content changed
        if old_hash and new_hash and old_hash != new_hash:
            return True
        
        # If we only have simhashes and distance > threshold, content changed
        if old_simhash is not None and new_simhash is not None:
            distance = Simhash.hamming_distance(old_simhash, new_simhash)
            return distance > threshold
        
        # Default: assume changed if we can't determine
        return True
    
    def jaccard_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate Jaccard similarity between two content strings.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Jaccard similarity (0.0 to 1.0)
        """
        features1 = set(self._extract_features(content1))
        features2 = set(self._extract_features(content2))
        
        if not features1 and not features2:
            return 1.0
        
        intersection = len(features1 & features2)
        union = len(features1 | features2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def detect_content_type(self, content: str, content_type_header: Optional[str] = None) -> str:
        """
        Detect content type from content or header.
        
        Args:
            content: Content string
            content_type_header: Content-Type HTTP header
            
        Returns:
            Content type string (e.g., "text/html", "application/json")
        """
        if content_type_header:
            # Extract MIME type from header
            mime = content_type_header.split(';')[0].strip().lower()
            return mime
        
        # Heuristic detection from content
        content_lower = content.lower().strip()
        
        if content_lower.startswith('<!doctype') or content_lower.startswith('<html'):
            return "text/html"
        elif content_lower.startswith('{') or content_lower.startswith('['):
            return "application/json"
        elif content_lower.startswith('<?xml'):
            return "application/xml"
        else:
            return "text/plain"








