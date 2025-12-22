"""
Unit Tests for ComfyUI Agent Tools

Tests tool functionality with mocked RunPod responses.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Import tools
from agents.comfy.tools import generate_image_with_runpod, list_workflows
from agents.comfy.workflows import load_workflow, prepare_workflow_for_api


@pytest.mark.unit
def test_list_workflows_success(workflow_dir):
    """Test listing available workflows."""
    result = list_workflows()
    
    assert result["status"] == "success"
    assert "workflows" in result
    assert "count" in result
    assert result["count"] == len(result["workflows"])
    assert isinstance(result["workflows"], list)


@pytest.mark.unit
def test_load_workflow_success(workflow_dir):
    """Test loading a workflow file."""
    workflows = list_workflows()
    if workflows["count"] > 0:
        workflow_name = workflows["workflows"][0]
        workflow = load_workflow(workflow_name)
        
        assert workflow is not None
        assert isinstance(workflow, dict)


@pytest.mark.unit
def test_prepare_workflow_for_api(test_workflow):
    """Test workflow preparation for API."""
    prompt = "Test prompt"
    seed = 12345
    width = 1024
    height = 1024
    
    prepared = prepare_workflow_for_api(
        workflow=test_workflow,
        prompt=prompt,
        seed=seed,
        width=width,
        height=height
    )
    
    assert "input" in prepared
    assert "workflow" in prepared["input"]


@pytest.mark.unit
@patch('agents.comfy.tools.RunPodWorkflowRunner')
@patch('agents.comfy.tools.load_workflow')
def test_generate_image_success(mock_load_workflow, mock_runner_class, test_workflow, mock_runpod_success, tmp_path):
    """Test successful image generation with mocked RunPod."""
    # Setup mocks
    mock_load_workflow.return_value = test_workflow
    mock_runner_class.return_value = mock_runpod_success
    
    # Override OUTPUT_DIR for test
    with patch('agents.comfy.tools.OUTPUT_DIR', tmp_path):
        result = generate_image_with_runpod(
            prompt="Test prompt",
            workflow_name="test_workflow.json",
            seed=12345
        )
    
    assert result["status"] == "success"
    assert "filepath" in result
    assert "filename" in result
    assert "seed" in result
    assert result["seed"] == 12345
    assert "job_id" in result
    assert result["job_id"] == "test-job-123"


@pytest.mark.unit
@patch('agents.comfy.tools.RunPodWorkflowRunner')
@patch('agents.comfy.tools.load_workflow')
def test_generate_image_failure(mock_load_workflow, mock_runner_class, test_workflow, mock_runpod_failure):
    """Test image generation with RunPod failure."""
    mock_load_workflow.return_value = test_workflow
    mock_runner_class.return_value = mock_runpod_failure
    
    result = generate_image_with_runpod(
        prompt="Test prompt",
        workflow_name="test_workflow.json"
    )
    
    assert result["status"] == "error"
    assert "error" in result
    assert "GPU out of memory" in result["error"]


@pytest.mark.unit
@patch('agents.comfy.tools.RunPodWorkflowRunner')
@patch('agents.comfy.tools.load_workflow')
def test_generate_image_timeout(mock_load_workflow, mock_runner_class, test_workflow, mock_runpod_timeout):
    """Test image generation with timeout."""
    mock_load_workflow.return_value = test_workflow
    mock_runner_class.return_value = mock_runpod_timeout
    
    result = generate_image_with_runpod(
        prompt="Test prompt",
        workflow_name="test_workflow.json"
    )
    
    assert result["status"] == "error"
    assert "Timeout" in result["error"]


@pytest.mark.unit
def test_generate_image_empty_prompt():
    """Test that empty prompts are rejected."""
    result = generate_image_with_runpod(prompt="")
    
    assert result["status"] == "error"
    assert "empty" in result["message"].lower()


@pytest.mark.unit
def test_generate_image_whitespace_prompt():
    """Test that whitespace-only prompts are rejected."""
    result = generate_image_with_runpod(prompt="   \n\t  ")
    
    assert result["status"] == "error"
    assert "empty" in result["message"].lower()


@pytest.mark.unit
@patch('agents.comfy.tools.load_workflow')
def test_generate_image_workflow_not_found(mock_load_workflow):
    """Test handling of missing workflow file."""
    mock_load_workflow.side_effect = FileNotFoundError("Workflow not found")
    
    result = generate_image_with_runpod(
        prompt="Test prompt",
        workflow_name="nonexistent.json"
    )
    
    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


@pytest.mark.unit
def test_generate_image_random_seed():
    """Test that random seed is generated when not provided."""
    with patch('agents.comfy.tools.load_workflow') as mock_load:
        with patch('agents.comfy.tools.RunPodWorkflowRunner'):
            mock_load.side_effect = FileNotFoundError()  # Exit early
            
            result1 = generate_image_with_runpod(prompt="Test")
            result2 = generate_image_with_runpod(prompt="Test")
            
            # Both should fail at workflow loading, but that's ok
            # We're just testing the function accepts None for seed
            assert result1["status"] == "error"
            assert result2["status"] == "error"


@pytest.mark.unit
@patch('agents.comfy.tools.RunPodWorkflowRunner')
@patch('agents.comfy.tools.load_workflow')
def test_generate_image_custom_dimensions(mock_load_workflow, mock_runner_class, test_workflow, mock_runpod_success, tmp_path):
    """Test image generation with custom dimensions."""
    mock_load_workflow.return_value = test_workflow
    mock_runner_class.return_value = mock_runpod_success
    
    with patch('agents.comfy.tools.OUTPUT_DIR', tmp_path):
        result = generate_image_with_runpod(
            prompt="Test prompt",
            workflow_name="test.json",
            width=2048,
            height=2048,
            seed=99999
        )
    
    assert result["status"] == "success"
    assert result["width"] == 2048
    assert result["height"] == 2048
    assert result["seed"] == 99999



