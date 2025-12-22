"""
ComfyUI Workflow Batch Test Runner

Simple, notebook-first batch testing framework for ComfyUI workflows.
Provides pass/fail validation with parallel execution and resume capability.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "notebooks" / "comfy"))

from runpod_runner import RunPodWorkflowRunner
from .config import RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID, OUTPUT_DIR
from .workflows import load_workflow, prepare_workflow_for_api
from .debug import get_logger, Timer

logger = get_logger(__name__)


class BatchTestRunner:
    """
    Batch test runner for ComfyUI workflows.
    
    Executes multiple workflow tests in parallel with pass/fail validation.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize batch test runner.
        
        Args:
            output_dir: Directory for test results (default: outputs/batch_test_TIMESTAMP)
        """
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = OUTPUT_DIR / f"batch_test_{timestamp}"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results_file = self.output_dir / "results.json"
        self.logs_dir = self.output_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.runner = RunPodWorkflowRunner(
            api_key=RUNPOD_API_KEY,
            endpoint_id=RUNPOD_ENDPOINT_ID
        )
        
        logger.info(f"BatchTestRunner initialized: {self.output_dir}")
    
    def load_config(self, config_path: Path) -> List[Dict[str, Any]]:
        """
        Load test configuration from JSON file.
        
        Args:
            config_path: Path to test_config.json
            
        Returns:
            List of test case dictionaries
        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        tests = config.get("tests", [])
        logger.info(f"Loaded {len(tests)} test cases from {config_path}")
        return tests
    
    def _apply_input_overrides(self, workflow: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply input overrides to workflow using dot notation.
        
        Args:
            workflow: Workflow dictionary
            inputs: Input overrides in dot notation (e.g., "38.inputs.prompt")
            
        Returns:
            Modified workflow
        """
        workflow_nodes = workflow.get("input", {}).get("workflow", workflow)
        
        for key_path, value in inputs.items():
            parts = key_path.split(".")
            if len(parts) >= 2:
                node_id = parts[0]
                if node_id in workflow_nodes:
                    node = workflow_nodes[node_id]
                    if "inputs" not in node:
                        node["inputs"] = {}
                    
                    if len(parts) == 2 and parts[1] == "inputs":
                        continue
                    elif len(parts) >= 3 and parts[1] == "inputs":
                        input_key = ".".join(parts[2:])
                        node["inputs"][input_key] = value
                    else:
                        node["inputs"][parts[1]] = value
        
        if "input" not in workflow:
            workflow = {"input": {"workflow": workflow_nodes}}
        else:
            workflow["input"]["workflow"] = workflow_nodes
        
        return workflow
    
    def _validate_image_not_black(self, image_path: Path, threshold: int = 10) -> bool:
        """Check image is not all black/corrupted."""
        try:
            from PIL import Image
            import numpy as np
            
            img = Image.open(image_path).convert('RGB')
            mean = np.array(img).mean()
            return mean > threshold
        except Exception as e:
            logger.warning(f"Image validation failed: {e}")
            return False
    
    def _validate_result(self, result: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate test result and determine pass/fail.
        
        Args:
            result: Result from RunPod execution
            test_case: Original test case configuration
            
        Returns:
            Result dict with status and validation details
        """
        validation = {
            "job_completed": False,
            "images_saved": False,
            "image_not_black": False
        }
        
        if result.get("status") == "success":
            validation["job_completed"] = True
            
            filepath = result.get("filepath")
            if filepath and Path(filepath).exists():
                validation["images_saved"] = True
                validation["image_not_black"] = self._validate_image_not_black(Path(filepath))
        
        all_passed = all(validation.values())
        result["validation"] = validation
        result["status"] = "PASS" if all_passed else "FAIL"
        
        if not all_passed:
            failures = [k for k, v in validation.items() if not v]
            result["error"] = f"Validation failed: {', '.join(failures)}"
        
        return result
    
    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test case.
        
        Args:
            test_case: Test case configuration
            
        Returns:
            Test result with status, timing, and validation
        """
        test_id = test_case.get("id", "unknown")
        start_time = time.time()
        
        log_file = self.logs_dir / f"{test_id}.log"
        
        try:
            logger.info(f"[{test_id}] Starting test: {test_case.get('workflow')}")
            
            workflow_name = test_case.get("workflow")
            if not workflow_name:
                return {
                    "test_id": test_id,
                    "status": "FAIL",
                    "error": "No workflow specified",
                    "elapsed": time.time() - start_time
                }
            
            workflow = load_workflow(workflow_name)
            
            inputs = test_case.get("inputs", {})
            if inputs:
                workflow = self._apply_input_overrides(workflow, inputs)
            
            workflow_payload = prepare_workflow_for_api(
                workflow=workflow,
                prompt=test_case.get("prompt", "test prompt"),
                seed=test_case.get("seed"),
                width=test_case.get("width", 1280),
                height=test_case.get("height", 1440)
            )
            
            timeout = test_case.get("timeout", 300)
            max_polls = timeout // 5
            
            job_id = self.runner.submit_job(workflow_payload)
            if not job_id:
                return {
                    "test_id": test_id,
                    "status": "FAIL",
                    "error": "Failed to submit job",
                    "elapsed": time.time() - start_time
                }
            
            status_data = self.runner.poll_status(job_id, max_polls=max_polls, poll_interval=5)
            
            if not status_data or status_data.get("status") != "COMPLETED":
                error_msg = status_data.get("error", "Timeout") if status_data else "Timeout"
                return {
                    "test_id": test_id,
                    "status": "FAIL",
                    "error": error_msg,
                    "job_id": job_id,
                    "elapsed": time.time() - start_time
                }
            
            images = status_data.get("output", {}).get("images", [])
            if not images:
                return {
                    "test_id": test_id,
                    "status": "FAIL",
                    "error": "No images in output",
                    "job_id": job_id,
                    "elapsed": time.time() - start_time
                }
            
            image_data = images[0].get("data")
            if not image_data:
                return {
                    "test_id": test_id,
                    "status": "FAIL",
                    "error": "No image data in output",
                    "job_id": job_id,
                    "elapsed": time.time() - start_time
                }
            
            import base64
            from PIL import Image
            from io import BytesIO
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
            
            filename = f"{test_id}_{int(time.time())}.png"
            filepath = self.output_dir / filename
            image.save(filepath)
            
            result = {
                "test_id": test_id,
                "status": "success",
                "filepath": str(filepath),
                "filename": filename,
                "job_id": job_id,
                "elapsed": time.time() - start_time
            }
            
            result = self._validate_result(result, test_case)
            logger.info(f"[{test_id}] {result['status']} ({result['elapsed']:.1f}s)")
            
            return result
            
        except Exception as e:
            logger.exception(f"[{test_id}] Test failed with exception: {e}")
            return {
                "test_id": test_id,
                "status": "FAIL",
                "error": str(e),
                "elapsed": time.time() - start_time
            }
    
    def run_batch(self, test_cases: List[Dict[str, Any]], max_workers: int = 4, resume: bool = True) -> Dict[str, Any]:
        """
        Execute batch of tests in parallel.
        
        Args:
            test_cases: List of test case configurations
            max_workers: Number of parallel workers
            resume: Skip tests that already have results
            
        Returns:
            Summary dictionary with all results
        """
        existing_results = {}
        if resume and self.results_file.exists():
            with open(self.results_file, 'r') as f:
                existing_results = json.load(f).get("results", {})
            logger.info(f"Resuming: {len(existing_results)} tests already completed")
        
        results = {}
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for test_case in test_cases:
                test_id = test_case.get("id", "unknown")
                if resume and test_id in existing_results:
                    results[test_id] = existing_results[test_id]
                    logger.info(f"[{test_id}] Skipping (already completed)")
                    continue
                
                future = executor.submit(self.run_test, test_case)
                futures[future] = test_id
            
            for future in as_completed(futures):
                test_id = futures[future]
                try:
                    result = future.result()
                    results[test_id] = result
                    
                    summary = {
                        "timestamp": datetime.now().isoformat(),
                        "total": len(test_cases),
                        "completed": len(results),
                        "results": results
                    }
                    
                    with open(self.results_file, 'w') as f:
                        json.dump(summary, f, indent=2)
                    
                except Exception as e:
                    logger.error(f"[{test_id}] Future failed: {e}")
                    results[test_id] = {
                        "test_id": test_id,
                        "status": "FAIL",
                        "error": str(e),
                        "elapsed": 0
                    }
        
        total_elapsed = time.time() - start_time
        passed = sum(1 for r in results.values() if r.get("status") == "PASS")
        failed = len(results) - passed
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "elapsed_seconds": total_elapsed,
            "results": results
        }
        
        with open(self.results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Batch complete: {passed} passed, {failed} failed in {total_elapsed:.1f}s")
        
        return summary





