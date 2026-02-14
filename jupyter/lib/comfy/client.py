"""Minimal Comfy client interface (placeholder)

This module should provide a small API for:
- building workflow JSON
- submitting workflows to a running ComfyUI instance
- polling for results

We'll flesh this out during Phase 1.
"""
from typing import Dict, Any

class ComfyClient:
    def __init__(self, host: str = 'http://127.0.0.1', port: int = 8188):
        self.base_url = f"{host}:{port}"

    def build_tryon_workflow(self, person_path: str, garment_path: str, out_path: str, **kwargs) -> Dict[str, Any]:
        """Return a JSON-serializable dict representing a ComfyUI workflow.
        This is a placeholder showing required keys; actual node specs will be added later.
        """
        workflow = {
            "nodes": [
                {"type": "LoadImage", "args": {"path": person_path}},
                {"type": "LoadImage", "args": {"path": garment_path}},
                {"type": "ImageStitch", "args": {}},
                {"type": "QwenImageEdit", "args": {"prompt": kwargs.get('prompt', '')}},
                {"type": "KSampler", "args": {"steps": kwargs.get('steps', 8)}},
                {"type": "SaveImage", "args": {"path": out_path}},
            ]
        }
        return workflow

    def submit_workflow(self, workflow: Dict[str, Any]) -> str:
        """Submit the workflow to ComfyUI and return a run id (placeholder)."""
        # TODO: implement HTTP POST to /api/workflows or websocket submission
        print('Submitting workflow (placeholder)')
        return 'run-1234'

    def poll_result(self, run_id: str, timeout: int = 300) -> str:
        """Poll for the result; return output path or URL (placeholder)."""
        print(f'Polling for {run_id} (placeholder)')
        return '/tmp/output.png'
