"""
Pytest Configuration and Fixtures for ComfyUI Agent Tests

Provides reusable fixtures for mocking RunPod, creating test sessions,
and setting up test workflows.
"""

import pytest
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load test environment variables
load_dotenv(project_root / ".env")

from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService


@pytest.fixture(scope="session")
def project_root_path():
    """Get project root directory."""
    return project_root


@pytest.fixture(scope="session")
def workflow_dir(project_root_path):
    """Get workflow directory."""
    return project_root_path / "Datasets" / "Comfy_Workflow"


@pytest.fixture
def test_workflow():
    """Provide a minimal test workflow structure."""
    return {
        "nodes": [
            {
                "id": 1,
                "type": "UNETLoader",
                "inputs": {"unet_name": "z-image_turbo_bf16.safetensors"}
            },
            {
                "id": 6,
                "type": "CLIPTextEncode",
                "inputs": {"text": "test prompt"}
            },
            {
                "id": 67,
                "type": "RandomNoise",
                "inputs": {"noise_seed": 12345}
            },
            {
                "id": 72,
                "type": "EmptyLatentImage",
                "inputs": {"width": 1280, "height": 1440, "batch_size": 1}
            }
        ]
    }


@pytest.fixture
def mock_runpod_success():
    """Mock successful RunPod workflow runner."""
    mock_runner = Mock()
    mock_runner.submit_job = Mock(return_value="test-job-123")
    mock_runner.poll_status = Mock(return_value={
        "status": "COMPLETED",
        "output": {
            "images": [{
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="  # 1x1 red pixel
            }]
        }
    })
    return mock_runner


@pytest.fixture
def mock_runpod_failure():
    """Mock failed RunPod workflow runner."""
    mock_runner = Mock()
    mock_runner.submit_job = Mock(return_value="test-job-456")
    mock_runner.poll_status = Mock(return_value={
        "status": "FAILED",
        "error": "GPU out of memory"
    })
    return mock_runner


@pytest.fixture
def mock_runpod_timeout():
    """Mock timed out RunPod workflow runner."""
    mock_runner = Mock()
    mock_runner.submit_job = Mock(return_value="test-job-789")
    mock_runner.poll_status = Mock(return_value=None)  # Timeout
    return mock_runner


@pytest.fixture
async def session_service():
    """Provide in-memory session service for tests."""
    return InMemorySessionService()


@pytest.fixture
async def artifact_service():
    """Provide in-memory artifact service for tests."""
    return InMemoryArtifactService()


@pytest.fixture
async def test_session(session_service):
    """Create a test session."""
    session = await session_service.create_session(
        app_name="comfyui_test",
        user_id="test_user"
    )
    return session


@pytest.fixture
def sample_prompts():
    """Provide sample prompts for testing."""
    return {
        "simple": "A red apple",
        "complex": "A cyberpunk gopher astronaut floating in space, digital art",
        "chinese": "一只赛博朋克风格的地鼠宇航员漂浮在太空中，数字艺术",
        "empty": "",
        "long": "A" * 1000  # Very long prompt
    }


@pytest.fixture
def expected_enhanced_prompt():
    """Expected enhanced prompt structure (Chinese)."""
    return "一个详细描述的视觉场景..."


@pytest.fixture
def mock_environment_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("RUNPOD_API_KEY", "test-api-key")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "test-endpoint")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("COMFY_DEBUG", "0")  # Disable debug in tests


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with ADK"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests that require API keys"
    )



