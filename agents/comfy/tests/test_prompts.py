"""
Unit Tests for Prompt Templates

Validates that prompt templates don't contain unresolved variables
and follow ADK template guidelines.
"""

import pytest
from agents.comfy.prompts import ZIT_PROMPT_TEMPLATE, WORKFLOW_SELECTOR_INSTRUCTION


@pytest.mark.unit
def test_zit_prompt_template_no_unresolved_vars():
    """Test that ZIT prompt template doesn't have unresolved {var} placeholders."""
    # These would cause KeyError in ADK if present
    assert "{prompt}" not in ZIT_PROMPT_TEMPLATE, \
        "ZIT_PROMPT_TEMPLATE contains unresolved {prompt} variable"
    assert "{user_input}" not in ZIT_PROMPT_TEMPLATE, \
        "ZIT_PROMPT_TEMPLATE contains unresolved {user_input} variable"


@pytest.mark.unit
def test_workflow_selector_no_unresolved_vars():
    """Test that workflow selector template doesn't have unresolved variables."""
    assert "{workflow_list}" not in WORKFLOW_SELECTOR_INSTRUCTION, \
        "WORKFLOW_SELECTOR_INSTRUCTION contains unresolved {workflow_list} variable"
    assert "{user_request}" not in WORKFLOW_SELECTOR_INSTRUCTION, \
        "WORKFLOW_SELECTOR_INSTRUCTION contains unresolved {user_request} variable"
    assert "{enhanced_prompt}" not in WORKFLOW_SELECTOR_INSTRUCTION, \
        "WORKFLOW_SELECTOR_INSTRUCTION contains unresolved {enhanced_prompt} variable"


@pytest.mark.unit
def test_zit_template_contains_methodology():
    """Test that ZIT template includes key methodology components."""
    # Check for Chinese instructions (Z-Image Turbo is Chinese-first)
    assert "你是一位" in ZIT_PROMPT_TEMPLATE, \
        "ZIT template should contain Chinese instructions"
    assert "视觉" in ZIT_PROMPT_TEMPLATE, \
        "ZIT template should reference visual description"


@pytest.mark.unit
def test_workflow_selector_contains_instructions():
    """Test that workflow selector has proper instructions."""
    assert "ComfyUI" in WORKFLOW_SELECTOR_INSTRUCTION, \
        "Workflow selector should reference ComfyUI"
    assert "workflow" in WORKFLOW_SELECTOR_INSTRUCTION.lower(), \
        "Workflow selector should mention workflows"
    assert "list_workflows" in WORKFLOW_SELECTOR_INSTRUCTION, \
        "Workflow selector should instruct to call list_workflows tool"


@pytest.mark.unit
def test_templates_are_non_empty():
    """Test that templates are not empty strings."""
    assert len(ZIT_PROMPT_TEMPLATE.strip()) > 0, \
        "ZIT_PROMPT_TEMPLATE should not be empty"
    assert len(WORKFLOW_SELECTOR_INSTRUCTION.strip()) > 0, \
        "WORKFLOW_SELECTOR_INSTRUCTION should not be empty"


@pytest.mark.unit
def test_templates_are_strings():
    """Test that templates are string types."""
    assert isinstance(ZIT_PROMPT_TEMPLATE, str), \
        "ZIT_PROMPT_TEMPLATE should be a string"
    assert isinstance(WORKFLOW_SELECTOR_INSTRUCTION, str), \
        "WORKFLOW_SELECTOR_INSTRUCTION should be a string"



