"""
Metadata Parser for ComfyUI Workflows

Parses ComfyUI workflow JSON to extract structured prompt and parameter data.
"""

import json
import re
from typing import Dict, Any, Optional, List


class MetadataParser:
    """Parses ComfyUI workflow metadata into structured format."""

    def __init__(self):
        """Initialize the metadata parser."""
        pass

    def parse_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse ComfyUI workflow JSON to extract prompts and parameters.

        Args:
            workflow_data: Workflow JSON dictionary

        Returns:
            Dictionary with parsed structured data
        """
        result = {
            'positive_prompt': '',
            'negative_prompt': '',
            'model_name': None,
            'seed': None,
            'cfg': None,
            'steps': None,
            'sampler_name': None,
            'scheduler': None,
            'width': None,
            'height': None,
        }
        
        if not isinstance(workflow_data, dict):
            return result
        
        # Find CLIPTextEncode nodes for prompts
        for node_id, node_data in workflow_data.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            # Extract positive prompt from CLIPTextEncode nodes
            if class_type == 'CLIPTextEncode':
                text = inputs.get('text', '')
                # Heuristic: negative prompts often contain "bad", "worst", "blurry", etc.
                if any(word in text.lower() for word in ['bad', 'worst', 'blurry', 'deformed', 'low quality']):
                    if not result['negative_prompt']:
                        result['negative_prompt'] = text
                else:
                    if not result['positive_prompt']:
                        result['positive_prompt'] = text
            
            # Extract prompt from NanoBananaAIO nodes
            elif class_type == 'NanoBananaAIO':
                prompt_text = inputs.get('prompt', '')
                if prompt_text and not result['positive_prompt']:
                    result['positive_prompt'] = prompt_text
                    # Also extract model name if available
                    if not result['model_name']:
                        result['model_name'] = inputs.get('model_name')
            
            # Extract sampler parameters
            elif class_type == 'KSampler' or class_type == 'KSamplerAdvanced':
                result['seed'] = inputs.get('seed', inputs.get('noise_seed'))
                result['steps'] = inputs.get('steps')
                result['cfg'] = inputs.get('cfg', inputs.get('cfg_scale'))
                result['sampler_name'] = inputs.get('sampler_name')
                result['scheduler'] = inputs.get('scheduler')
            
            # Extract model name
            elif class_type in ['CheckpointLoaderSimple', 'CheckpointLoader']:
                result['model_name'] = inputs.get('ckpt_name')
            
            # Extract dimensions
            elif class_type in ['EmptyLatentImage', 'EmptySD3LatentImage']:
                result['width'] = inputs.get('width')
                result['height'] = inputs.get('height')
        
        return result

    def parse_prompt_text(self, prompt_text: str) -> Dict[str, str]:
        """
        Parse plain text prompt into positive/negative components.

        Args:
            prompt_text: Raw prompt text

        Returns:
            Dictionary with 'positive' and 'negative' keys
        """
        # Simple heuristic: check for common negative prompt patterns
        negative_keywords = ['negative:', 'neg:', 'not:', 'avoid:', 'bad', 'worst']
        
        prompt_lower = prompt_text.lower()
        for keyword in negative_keywords:
            if keyword in prompt_lower:
                parts = re.split(f'{keyword}', prompt_lower, flags=re.IGNORECASE, maxsplit=1)
                if len(parts) == 2:
                    return {
                        'positive': parts[0].strip(),
                        'negative': parts[1].strip()
                    }
        
        return {
            'positive': prompt_text.strip(),
            'negative': ''
        }

    def flatten_metadata(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten extracted metadata into a single-level dictionary for DataFrame.

        Args:
            extracted_data: Raw extracted metadata from extractor

        Returns:
            Flattened dictionary suitable for DataFrame
        """
        flattened = {
            'filename': extracted_data.get('filename', ''),
            'filepath': extracted_data.get('filepath', ''),
            'positive_prompt': '',
            'negative_prompt': '',
            'model_name': None,
            'seed': None,
            'cfg': None,
            'steps': None,
            'sampler_name': None,
            'scheduler': None,
            'width': None,
            'height': None,
        }
        
        # Parse workflow if present
        workflow = extracted_data.get('workflow')
        if workflow:
            if isinstance(workflow, dict):
                parsed = self.parse_workflow(workflow)
                flattened.update(parsed)
            elif isinstance(workflow, str):
                try:
                    workflow_dict = json.loads(workflow)
                    parsed = self.parse_workflow(workflow_dict)
                    flattened.update(parsed)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Parse prompt if present and not already extracted
        prompt = extracted_data.get('prompt')
        if prompt and not flattened['positive_prompt']:
            if isinstance(prompt, dict):
                # Might be a structured prompt object
                flattened['positive_prompt'] = prompt.get('positive', prompt.get('text', str(prompt)))
                flattened['negative_prompt'] = prompt.get('negative', '')
            elif isinstance(prompt, str):
                parsed = self.parse_prompt_text(prompt)
                flattened['positive_prompt'] = parsed['positive']
                flattened['negative_prompt'] = parsed['negative']
        
        return flattened

