"""Bot pattern detection system for identifying automated posting behavior."""

import re
import hashlib
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path

from bs4 import BeautifulSoup

from feed.storage.neo4j_connection import get_connection
from feed.crawler.content import ContentAnalyzer, Simhash


class BotPatternDetector:
    """Detects automated posting systems through pattern analysis."""

    def __init__(self, neo4j=None, simhash_threshold: int = 3):
        """
        Initialize bot pattern detector.

        Args:
            neo4j: Neo4j connection (optional, will create if None)
            simhash_threshold: Hamming distance threshold for near-duplicates
        """
        self.neo4j = neo4j or get_connection()
        self.content_analyzer = ContentAnalyzer(simhash_bits=64)
        self.simhash_threshold = simhash_threshold

    def analyze_cached_html(self, html_dir: Path) -> Dict:
        """
        Analyze all cached HTML files for bot patterns.

        Args:
            html_dir: Directory containing cached HTML files

        Returns:
            Analysis results with cross-thread matches and bot fingerprints
        """
        html_files = list(html_dir.glob("*.html"))
        print(f"Found {len(html_files)} cached HTML files")

        results = {
            "total_files": len(html_files),
            "total_posts": 0,
            "cross_thread_matches": [],
            "content_fingerprints": defaultdict(list),
            "bot_signatures": {},
            "posting_campaigns": [],
            "time_patterns": defaultdict(list),
        }

        for html_file in html_files:
            thread_data = self._parse_thread_html(html_file)
            if not thread_data:
                continue

            results["total_posts"] += len(thread_data["posts"])

            for post in thread_data["posts"]:
                post_signature = self._compute_post_signature(post)

                # Track content fingerprint
                content_hash = post_signature["content_hash"]
                results["content_fingerprints"][content_hash].append({
                    "file": html_file.name,
                    "thread_id": thread_data["thread_id"],
                    "board": thread_data["board"],
                    "post_no": post.get("no"),
                    "timestamp": post.get("time"),
                    "post_text": post_signature["text"],
                })

                results["time_patterns"][thread_data["thread_id"]].append({
                    "post_no": post.get("no"),
                    "timestamp": post.get("time"),
                    "content_hash": content_hash,
                    "simhash": post_signature["simhash"],
                })

        # Find cross-thread matches (same content in different threads)
        results["cross_thread_matches"] = self._find_cross_thread_matches(
            results["content_fingerprints"]
        )

        # Identify bot signatures from repetitive posting
        results["bot_signatures"] = self._identify_bot_signatures(
            results["content_fingerprints"],
            results["cross_thread_matches"]
        )

        # Detect posting campaigns
        results["posting_campaigns"] = self._detect_posting_campaigns(
            results["bot_signatures"],
            results["time_patterns"]
        )

        return results

    def _parse_thread_html(self, html_file: Path) -> Optional[Dict]:
        """
        Parse thread HTML to extract post data.

        Args:
            html_file: Path to HTML file

        Returns:
            Thread data with posts
        """
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract thread ID from filename
            filename = html_file.stem
            if '_' in filename:
                parts = filename.split('_')
                board = parts[0]
                thread_id = parts[1].split('.')[0] if '.' in parts[1] else parts[1]
            else:
                thread_id = filename
                board = 'unknown'

            posts = []

            # Parse all posts
            for post_div in soup.find_all('div', class_='postContainer'):
                post = self._extract_post_data(post_div)
                if post:
                    posts.append(post)

            return {
                "thread_id": thread_id,
                "board": board,
                "posts": posts,
            }

        except Exception as e:
            print(f"Error parsing {html_file}: {e}")
            return None

    def _extract_post_data(self, post_div) -> Optional[Dict]:
        """Extract data from a post div element."""
        try:
            # Get post ID
            post_info = post_div.find('div', class_='postInfo')
            if not post_info:
                return None

            subject = post_info.find('span', class_='subject')
            name = post_info.find('span', class_='name')
            tripcode = post_info.find('span', class_='tripcode')
            time_el = post_info.find('span', class_='dateTime')
            no_el = post_info.find('a', class_='post_no')

            post_content = post_div.find('blockquote', class_='postMessage')

            post = {
                "subject": subject.get_text(strip=True) if subject else None,
                "name": name.get_text(strip=True) if name else "Anonymous",
                "tripcode": tripcode.get_text(strip=True) if tripcode else None,
                "time": time_el.get_text(strip=True) if time_el else None,
                "no": no_el.get_text(strip=True) if no_el else None,
                "text": post_content.get_text(strip=True) if post_content else "",
                "images": self._extract_images(post_div),
            }

            return post

        except Exception as e:
            print(f"Error extracting post: {e}")
            return None

    def _extract_images(self, post_div) -> List[Dict]:
        """Extract image information from post."""
        images = []
        file_info = post_div.find('div', class_='fileText')
        if file_info:
            images.append({
                "filename": file_info.get_text(strip=True),
            })
        return images

    def _compute_post_signature(self, post: Dict) -> Dict:
        """
        Compute signature for a post.

        Args:
            post: Post data dictionary

        Returns:
            Signature with content hash, simhash, and cleaned text
        """
        # Combine text fields for signature
        text_parts = []
        if post.get("subject"):
            text_parts.append(post["subject"])
        if post.get("text"):
            text_parts.append(post["text"])

        full_text = " ".join(text_parts).strip()

        # Clean text (normalize whitespace, etc.)
        cleaned_text = re.sub(r'\s+', ' ', full_text)

        content_hash = self.content_analyzer.compute_content_hash(cleaned_text)
        simhash = self.content_analyzer.compute_simhash(cleaned_text)

        return {
            "content_hash": content_hash,
            "simhash": simhash,
            "text": cleaned_text,
            "text_length": len(cleaned_text),
            "has_image": len(post.get("images", [])) > 0,
        }

    def _find_cross_thread_matches(self, fingerprints: Dict) -> List[Dict]:
        """
        Find content that appears in multiple threads.

        Args:
            fingerprints: Dictionary mapping content_hash to list of occurrences

        Returns:
            List of cross-thread matches
        """
        matches = []

        for content_hash, occurrences in fingerprints.items():
            if len(occurrences) < 2:
                continue

            # Group by thread
            threads = {}
            for occ in occurrences:
                thread_id = occ["thread_id"]
                if thread_id not in threads:
                    threads[thread_id] = []
                threads[thread_id].append(occ)

            if len(threads) >= 2:
                matches.append({
                    "content_hash": content_hash,
                    "occurrence_count": len(occurrences),
                    "thread_count": len(threads),
                    "threads": list(threads.keys()),
                    "text": occurrences[0]["post_text"],
                    "occurrences": occurrences,
                })

        # Sort by occurrence count (most reposted first)
        matches.sort(key=lambda x: x["occurrence_count"], reverse=True)

        return matches

    def _identify_bot_signatures(
        self,
        fingerprints: Dict,
        cross_thread_matches: List[Dict]
    ) -> Dict:
        """
        Identify bot signatures from repetitive posting patterns.

        Args:
            fingerprints: Content fingerprint dictionary
            cross_thread_matches: Cross-thread matches

        Returns:
            Bot signatures with confidence scores
        """
        signatures = {}

        # Build signatures from cross-thread matches
        for match in cross_thread_matches:
            # Signature ID based on content hash
            sig_id = match["content_hash"][:16]

            signatures[sig_id] = {
                "content_hash": match["content_hash"],
                "post_count": match["occurrence_count"],
                "thread_count": match["thread_count"],
                "threads": match["threads"],
                "sample_text": match["text"][:200],
                "confidence": self._calculate_bot_confidence(match),
                "posting_pattern": self._analyze_posting_pattern(match["occurrences"]),
            }

        # Sort by confidence
        signatures = dict(sorted(
            signatures.items(),
            key=lambda x: x[1]["confidence"],
            reverse=True
        ))

        return signatures

    def _calculate_bot_confidence(self, match: Dict) -> float:
        """
        Calculate confidence score that this is bot activity.

        Args:
            match: Cross-thread match data

        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.0

        # More occurrences = higher confidence
        if match["occurrence_count"] >= 10:
            score += 0.4
        elif match["occurrence_count"] >= 5:
            score += 0.3
        elif match["occurrence_count"] >= 3:
            score += 0.2

        # More threads = higher confidence (cross-thread spam)
        if match["thread_count"] >= 5:
            score += 0.4
        elif match["thread_count"] >= 3:
            score += 0.3
        elif match["thread_count"] >= 2:
            score += 0.2

        # Pattern indicators
        text = match["text"].lower()
        # Generic concern troll language
        if any(phrase in text for phrase in [
            "imagine if this was your",
            "stop doing this",
            "fucking disgusting",
            "creeps",
            "just put yourself",
        ]):
            score += 0.2

        # Cap at 1.0
        return min(score, 1.0)

    def _analyze_posting_pattern(self, occurrences: List[Dict]) -> Dict:
        """
        Analyze temporal posting pattern.

        Args:
            occurrences: List of post occurrences

        Returns:
            Pattern analysis
        """
        timestamps = [occ.get("timestamp") for occ in occurrences if occ.get("timestamp")]

        # Try to parse timestamps
        parsed_times = []
        for ts in timestamps:
            try:
                # 4chan timestamp format: "12/31/25(Wed)09:41:17"
                if ts and '(' in ts:
                    time_part = ts.split(')')[1]
                    parsed_times.append(time_part)
            except:
                pass

        return {
            "total_occurrences": len(occurrences),
            "unique_threads": len(set(occ["thread_id"] for occ in occurrences)),
            "timestamp_count": len(parsed_times),
            "sample_timestamps": parsed_times[:5],
        }

    def _detect_posting_campaigns(
        self,
        bot_signatures: Dict,
        time_patterns: Dict
    ) -> List[Dict]:
        """
        Detect coordinated posting campaigns.

        Args:
            bot_signatures: Bot signature dictionary
            time_patterns: Time pattern data

        Returns:
            List of detected campaigns
        """
        campaigns = []

        # Group signatures by thread overlap
        thread_to_sigs = defaultdict(list)
        for sig_id, sig_data in bot_signatures.items():
            for thread_id in sig_data["threads"]:
                thread_to_sigs[thread_id].append(sig_id)

        # Find campaigns (multiple bot signatures in same threads)
        for thread_id, sig_ids in thread_to_sigs.items():
            if len(sig_ids) >= 2:
                campaign = {
                    "thread_id": thread_id,
                    "signature_count": len(sig_ids),
                    "signatures": sig_ids,
                    "confidence": sum(
                        bot_signatures[sig_id]["confidence"]
                        for sig_id in sig_ids
                    ) / len(sig_ids),
                }
                campaigns.append(campaign)

        # Sort by signature count
        campaigns.sort(key=lambda x: x["signature_count"], reverse=True)

        return campaigns

    def print_analysis_report(self, results: Dict):
        """Print formatted analysis report."""
        print("\n" + "="*80)
        print("BOT PATTERN ANALYSIS REPORT")
        print("="*80)
        print(f"\nTotal files analyzed: {results['total_files']}")
        print(f"Total posts analyzed: {results['total_posts']}")
        print(f"Cross-thread matches found: {len(results['cross_thread_matches'])}")
        print(f"Bot signatures identified: {len(results['bot_signatures'])}")
        print(f"Posting campaigns detected: {len(results['posting_campaigns'])}")

        if results["bot_signatures"]:
            print("\n" + "-"*80)
            print("TOP BOT SIGNATURES")
            print("-"*80)
            for i, (sig_id, sig_data) in enumerate(
                list(results["bot_signatures"].items())[:10]
            ):
                print(f"\n#{i+1} Signature: {sig_id}")
                print(f"  Confidence: {sig_data['confidence']:.2f}")
                print(f"  Post count: {sig_data['post_count']}")
                print(f"  Thread count: {sig_data['thread_count']}")
                print(f"  Sample text: {sig_data['sample_text']}...")
                print(f"  Threads: {', '.join(sig_data['threads'][:5])}")

        if results["posting_campaigns"]:
            print("\n" + "-"*80)
            print("POSTING CAMPAIGNS (Multi-bot activity)")
            print("-"*80)
            for i, campaign in enumerate(results["posting_campaigns"][:5]):
                print(f"\nCampaign #{i+1}:")
                print(f"  Thread: {campaign['thread_id']}")
                print(f"  Bot signatures: {campaign['signature_count']}")
                print(f"  Campaign confidence: {campaign['confidence']:.2f}")
