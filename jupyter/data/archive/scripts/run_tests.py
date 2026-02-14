#!/usr/bin/env python3
"""
Simple test runner for ASR evaluation system.
"""

import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required test dependencies are available."""
    required_packages = [
        "pytest",
        "numpy", 
        "soundfile"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing test dependencies: {', '.join(missing)}")
        print("Install with: pip install pytest numpy soundfile")
        return False
    
    return True


def run_basic_availability_test():
    """Run basic model availability test without pytest."""
    print("=" * 50)
    print("BASIC MODEL AVAILABILITY TEST")
    print("=" * 50)
    
    try:
        from asr_evaluation.adapters.faster_whisper_adapter import FasterWhisperAdapter
        
        print("1. Testing adapter creation...")
        adapter = FasterWhisperAdapter(model_size="tiny")
        print("✅ Adapter created successfully")
        
        print("2. Testing model info...")
        info = adapter.get_model_info()
        print(f"✅ Model info: {info.name} v{info.version}")
        
        print("3. Testing model availability...")
        is_available = adapter.is_available()
        
        if is_available:
            print("✅ Model is available and loaded!")
            return True
        else:
            print("❌ Model not available")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def run_pytest():
    """Run full pytest suite."""
    print("=" * 50)
    print("RUNNING FULL TEST SUITE")
    print("=" * 50)
    
    if not check_dependencies():
        return False
    
    try:
        # Run pytest with coverage if available
        cmd = ["python", "-m", "pytest", "tests/", "-v"]
        
        # Try to add coverage
        try:
            import coverage
            cmd.extend(["--cov=asr_evaluation", "--cov-report=term-missing"])
        except ImportError:
            print("Note: Install 'coverage' for test coverage reports")
        
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Pytest execution failed: {e}")
        return False


def main():
    """Main test runner."""
    print("ASR Evaluation System - Test Runner")
    print("=" * 50)
    
    # Always run basic test first
    basic_success = run_basic_availability_test()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        print("\n")
        full_success = run_pytest()
        
        if basic_success and full_success:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
    else:
        if basic_success:
            print("\n✅ Basic availability test passed!")
            print("Run with --full for complete test suite")
            return 0
        else:
            print("\n❌ Basic test failed")
            return 1


if __name__ == "__main__":
    sys.exit(main())