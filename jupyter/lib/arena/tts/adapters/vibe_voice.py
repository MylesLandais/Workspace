"""VibeVoice cloud voice cloning backend via RunPod/ComfyUI."""

import json
import os
import time
from pathlib import Path

import numpy as np

from ..base import VoiceCloningBackend, VoiceCloneResult, VoicePrompt


class VibeVoiceBackend(VoiceCloningBackend):
    """Cloud voice cloning via VibeVoice on RunPod/ComfyUI."""

    def __init__(
        self,
        pod_id: str | None = None,
        api_key: str | None = None,
        comfyui_port: int = 8188,
    ):
        self.pod_id = pod_id or os.getenv("RUNPOD_POD_ID")
        self.api_key = api_key or os.getenv("RUNPOD_API_KEY")
        self.comfyui_port = comfyui_port
        self._ssh = None
        self._connected = False

    @property
    def name(self) -> str:
        return "VibeVoice-Large"

    @property
    def is_local(self) -> bool:
        return False

    def load(self) -> None:
        if self._connected:
            return

        if not self.pod_id:
            raise ValueError("pod_id required for VibeVoice backend")

        try:
            from runpod.cli.utils.ssh_cmd import SSHConnection

            self._ssh = SSHConnection(self.pod_id)
            self._connected = True
        except ImportError:
            raise ImportError("runpod CLI required: pip install runpod")

    def unload(self) -> None:
        self._ssh = None
        self._connected = False

    def _upload_audio(self, local_path: str | Path) -> str:
        """Upload reference audio to pod and return remote path."""
        local_path = Path(local_path)
        remote_path = f"/workspace/ComfyUI/input/{local_path.name}"
        self._ssh.put_file(str(local_path), remote_path)
        return remote_path

    def _download_audio(self, remote_path: str) -> np.ndarray:
        """Download generated audio from pod."""
        import tempfile

        import soundfile as sf

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            local_path = f.name

        self._ssh.get_file(remote_path, local_path)
        audio, sr = sf.read(local_path)
        Path(local_path).unlink()
        return audio, sr

    def _execute_workflow(
        self,
        text: str,
        ref_audio_remote: str,
        ref_text: str | None = None,
    ) -> tuple[str, float]:
        """Execute ComfyUI workflow and return output path and elapsed time."""
        start = time.perf_counter()

        workflow = {
            "last_node_id": 3,
            "last_link_id": 2,
            "nodes": [
                {
                    "id": 1,
                    "type": "VibeVoiceNode",
                    "pos": [100, 300],
                    "size": [300, 400],
                    "flags": {},
                    "order": 0,
                    "mode": 0,
                    "inputs": [],
                    "outputs": [
                        {
                            "name": "audio",
                            "type": "AUDIO",
                            "links": [1],
                            "slot_index": 0,
                        }
                    ],
                    "properties": {"Node name for S&R": "VibeVoiceNode"},
                    "widgets_values": [
                        ref_audio_remote,
                        text,
                        1.0,  # Guidance scale
                        50,  # Inference steps
                        0.8,  # Audio length
                        22050,  # Sample rate
                    ],
                },
                {
                    "id": 2,
                    "type": "SaveAudio",
                    "pos": [500, 300],
                    "size": [300, 200],
                    "flags": {},
                    "order": 1,
                    "mode": 0,
                    "inputs": [{"name": "audio", "type": "AUDIO", "link": 1}],
                    "outputs": [],
                    "properties": {"Node name for S&R": "SaveAudio"},
                    "widgets_values": ["vibe_voice_output"],
                },
            ],
            "links": [[1, 1, 0, 2, 0, "AUDIO"]],
            "groups": [],
            "config": {},
            "extra": {},
            "version": 0.4,
        }

        workflow_json = json.dumps({"prompt": workflow})
        curl_cmd = (
            f"curl -s -X POST http://localhost:{self.comfyui_port}/prompt "
            f"-H 'Content-Type: application/json' "
            f"-d '{workflow_json}'"
        )

        result = self._ssh.run_commands([curl_cmd])
        if not result or result[0].get("exit_code", 1) != 0:
            raise RuntimeError(f"Failed to submit workflow: {result}")

        response = json.loads(result[0].get("output", "{}"))
        prompt_id = response.get("prompt_id")
        if not prompt_id:
            raise RuntimeError("No prompt_id returned from ComfyUI")

        # Poll for completion
        max_wait = 120
        poll_interval = 2
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            history_cmd = f"curl -s http://localhost:{self.comfyui_port}/history"
            history_result = self._ssh.run_commands([history_cmd])

            if history_result and history_result[0].get("exit_code", 0) == 0:
                history = json.loads(history_result[0].get("output", "{}"))
                if prompt_id in history:
                    status = history[prompt_id].get("status", {})
                    if status.get("completed"):
                        outputs = history[prompt_id].get("outputs", {})
                        for node_outputs in outputs.values():
                            if "audio" in node_outputs:
                                audio_info = node_outputs["audio"][0]
                                filename = audio_info.get("filename", "")
                                output_path = f"/workspace/ComfyUI/output/{filename}"
                                generation_time = (time.perf_counter() - start) * 1000
                                return output_path, generation_time

        raise TimeoutError("Workflow execution timed out")

    def clone_voice(
        self,
        text: str,
        ref_audio: str | Path,
        ref_text: str | None = None,
        language: str = "English",
    ) -> VoiceCloneResult:
        self.load()

        remote_ref = self._upload_audio(ref_audio)
        output_path, elapsed_ms = self._execute_workflow(text, remote_ref, ref_text)
        audio, sr = self._download_audio(output_path)

        return VoiceCloneResult(
            audio=audio,
            sample_rate=sr,
            model_name=self.name,
            generation_time_ms=elapsed_ms,
        )

    def create_voice_prompt(
        self,
        ref_audio: str | Path,
        ref_text: str | None = None,
    ) -> VoicePrompt:
        # VibeVoice doesn't support cached prompts
        # Store reference info for re-upload each time
        return VoicePrompt(
            embedding=None,
            ref_audio_path=str(ref_audio),
            ref_text=ref_text,
            backend=self.name,
        )

    def generate_with_prompt(
        self,
        texts: list[str],
        voice_prompt: VoicePrompt,
        languages: list[str] | None = None,
    ) -> list[VoiceCloneResult]:
        # VibeVoice processes sequentially
        return [
            self.clone_voice(
                text=text,
                ref_audio=voice_prompt.ref_audio_path,
                ref_text=voice_prompt.ref_text,
            )
            for text in texts
        ]
