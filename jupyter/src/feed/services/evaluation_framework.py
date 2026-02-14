"""Evaluation framework for reverse lookup testing and benchmarking."""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

from ..storage.neo4j_connection import Neo4jConnection
from .reverse_image_search import ReverseImageSearch
from .video_watermark_detection import VideoIdentificationService
from .stash_integration import StashClient
from .forum_parser import VBulletinParser
from .wanted_metadata_tracker import WantedMetadataTracker
from .cross_source_verifier import CrossSourceVerifier


@dataclass
class TestCase:
    """Test case for evaluation."""
    test_id: str
    test_type: str  # 'image', 'video', 'performer', 'scene'
    input_data: Dict[str, Any]  # URL, path, name, etc.
    expected_result: Dict[str, Any]  # Expected matches, performers, etc.
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TestResult:
    """Result of a test case."""
    test_id: str
    passed: bool
    actual_result: Dict[str, Any]
    expected_result: Dict[str, Any]
    metrics: Dict[str, float]  # confidence, accuracy, etc.
    timestamp: datetime
    error: Optional[str] = None


@dataclass
class BenchmarkMetrics:
    """Benchmark metrics for evaluation."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    accuracy: float
    average_confidence: float
    processing_time: float
    source_breakdown: Dict[str, int]  # Matches by source
    detailed_results: List[TestResult]


class ReverseLookupEvaluator:
    """Evaluation framework for reverse lookup system."""
    
    def __init__(
        self,
        neo4j: Neo4jConnection,
        stash_url: Optional[str] = None
    ):
        """
        Initialize evaluator.
        
        Args:
            neo4j: Neo4j connection
            stash_url: Optional Stash instance URL
        """
        self.neo4j = neo4j
        self.reverse_search = ReverseImageSearch(neo4j=neo4j)
        self.video_service = VideoIdentificationService(
            neo4j=neo4j,
            stash_url=stash_url
        )
        self.wanted_tracker = WantedMetadataTracker(neo4j)
    
    def evaluate_image_lookup(
        self,
        test_cases: List[TestCase]
    ) -> BenchmarkMetrics:
        """
        Evaluate image lookup performance.
        
        Args:
            test_cases: List of test cases
            
        Returns:
            BenchmarkMetrics with results
        """
        results = []
        source_breakdown = {}
        
        for test_case in test_cases:
            image_url = test_case.input_data.get("image_url")
            if not image_url:
                continue
            
            start_time = datetime.now()
            
            # Run lookup
            lookup_result = self.reverse_search.check_if_crawled(image_url)
            
            # Also try exact matches
            if not lookup_result.found:
                lookup_result = self.reverse_search.find_exact_matches(image_url)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Evaluate result
            passed = lookup_result.found
            expected_found = test_case.expected_result.get("found", False)
            
            if passed == expected_found:
                passed = True
            else:
                passed = False
            
            # Calculate metrics
            confidence = 0.0
            if lookup_result.matches:
                confidence = max(m.confidence for m in lookup_result.matches)
            
            # Track source breakdown
            for match in lookup_result.matches:
                source = match.match_type
                source_breakdown[source] = source_breakdown.get(source, 0) + 1
            
            results.append(TestResult(
                test_id=test_case.test_id,
                passed=passed,
                actual_result={
                    "found": lookup_result.found,
                    "matches": len(lookup_result.matches),
                    "sources": [m.match_type for m in lookup_result.matches]
                },
                expected_result=test_case.expected_result,
                metrics={
                    "confidence": confidence,
                    "processing_time": elapsed
                },
                timestamp=datetime.now()
            ))
        
        # Calculate aggregate metrics
        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        avg_confidence = sum(r.metrics.get("confidence", 0) for r in results) / total if total > 0 else 0
        avg_time = sum(r.metrics.get("processing_time", 0) for r in results) / total if total > 0 else 0
        
        return BenchmarkMetrics(
            total_tests=total,
            passed_tests=passed_count,
            failed_tests=total - passed_count,
            accuracy=passed_count / total if total > 0 else 0,
            average_confidence=avg_confidence,
            processing_time=avg_time,
            source_breakdown=source_breakdown,
            detailed_results=results
        )
    
    def evaluate_video_identification(
        self,
        test_cases: List[TestCase]
    ) -> BenchmarkMetrics:
        """
        Evaluate video identification performance.
        
        Args:
            test_cases: List of test cases
            
        Returns:
            BenchmarkMetrics with results
        """
        results = []
        source_breakdown = {}
        
        for test_case in test_cases:
            video_path = test_case.input_data.get("video_path")
            watermark_patterns = test_case.input_data.get("watermark_patterns", [])
            
            if not video_path:
                continue
            
            start_time = datetime.now()
            
            # Run identification
            ident_result = self.video_service.identify_video(
                video_path,
                watermark_patterns=watermark_patterns
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Evaluate
            passed = ident_result.identified
            expected_identified = test_case.expected_result.get("identified", False)
            
            if passed == expected_identified:
                passed = True
            else:
                passed = False
            
            # Calculate metrics
            confidence = 0.0
            if ident_result.scene_matches:
                confidence = max(s.confidence for s in ident_result.scene_matches)
            
            # Track source breakdown
            for scene in ident_result.scene_matches:
                source = scene.match_type
                source_breakdown[source] = source_breakdown.get(source, 0) + 1
            
            results.append(TestResult(
                test_id=test_case.test_id,
                passed=passed,
                actual_result={
                    "identified": ident_result.identified,
                    "studio": ident_result.studio,
                    "scene_matches": len(ident_result.scene_matches),
                    "watermarks": len(ident_result.watermarks),
                    "sources": [s.match_type for s in ident_result.scene_matches]
                },
                expected_result=test_case.expected_result,
                metrics={
                    "confidence": confidence,
                    "processing_time": elapsed
                },
                timestamp=datetime.now()
            ))
        
        # Calculate aggregate metrics
        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        avg_confidence = sum(r.metrics.get("confidence", 0) for r in results) / total if total > 0 else 0
        avg_time = sum(r.metrics.get("processing_time", 0) for r in results) / total if total > 0 else 0
        
        return BenchmarkMetrics(
            total_tests=total,
            passed_tests=passed_count,
            failed_tests=total - passed_count,
            accuracy=passed_count / total if total > 0 else 0,
            average_confidence=avg_confidence,
            processing_time=avg_time,
            source_breakdown=source_breakdown,
            detailed_results=results
        )
    
    def evaluate_performer_cross_reference(
        self,
        performer_name: str,
        sources: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate cross-source verification for a performer.
        
        Args:
            performer_name: Performer name
            sources: List of sources to check
            
        Returns:
            Evaluation results
        """
        verifier = CrossSourceVerifier(self.neo4j)
        
        result = verifier.verify_performer_across_sources(performer_name, sources)
        
        # Check if performer is wanted
        wanted_info = self.wanted_tracker.cross_reference_sources(performer_name)
        
        return {
            "performer_name": performer_name,
            "sources_checked": sources,
            "source_results": result.get("sources", {}),
            "wanted_status": wanted_info,
            "has_content": wanted_info.get("has_content", False),
            "is_wanted": wanted_info.get("is_wanted", False)
        }
    
    def generate_benchmark_report(
        self,
        metrics: BenchmarkMetrics,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate benchmark report.
        
        Args:
            metrics: BenchmarkMetrics object
            output_path: Optional path to save report
            
        Returns:
            Report as JSON string
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": metrics.total_tests,
                "passed_tests": metrics.passed_tests,
                "failed_tests": metrics.failed_tests,
                "accuracy": metrics.accuracy,
                "average_confidence": metrics.average_confidence,
                "average_processing_time": metrics.processing_time,
                "source_breakdown": metrics.source_breakdown
            },
            "detailed_results": [
                {
                    "test_id": r.test_id,
                    "passed": r.passed,
                    "metrics": r.metrics,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in metrics.detailed_results
            ]
        }
        
        report_json = json.dumps(report, indent=2)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_json)
        
        return report_json

