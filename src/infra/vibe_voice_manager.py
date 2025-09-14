"""
VibeVoice Manager
Handles the deployment and management of the VibeVoice workflow for ComfyUI on RunPod.
"""

import os
import time
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import runpod
    from runpod.cli.utils.ssh_cmd import SSHConnection
except ImportError:
    # Handle case where runpod CLI is not available
    runpod = None
    SSHConnection = None

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ValidationResult:
    """Result of validating a VibeVoice setup."""
    success: bool
    instance_id: str
    checks: Dict[str, bool]
    errors: List[str]
    warnings: List[str]
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class VibeVoiceManager:
    """
    Manages VibeVoice workflow deployment and configuration on RunPod ComfyUI instances.
    """
    
    def __init__(self, runpod_api_key: str = None):
        """
        Initializes the VibeVoiceManager.
        
        Args:
            runpod_api_key: RunPod API key. If not provided, will be loaded from environment.
        """
        self.runpod_api_key = runpod_api_key or os.getenv("RUNPOD_API_KEY")
        if not self.runpod_api_key:
            raise ValueError("RUNPOD_API_KEY not found in environment or arguments.")
        
        if runpod:
            runpod.api_key = self.runpod_api_key
    
    def install_vibeVoice_nodes(self, instance_id: str) -> bool:
        """
        Installs the VibeVoice custom node on a ComfyUI instance.
        
        Args:
            instance_id: The RunPod instance ID
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        if not SSHConnection:
            print("SSHConnection not available. Cannot install VibeVoice nodes.")
            return False
            
        try:
            # Connect to the pod
            ssh = SSHConnection(instance_id)
            
            # Commands to install VibeVoice custom node
            commands = [
                "cd /workspace/ComfyUI/custom_nodes",
                "git clone https://github.com/wildminder/ComfyUI-VibeVoice.git",
                "cd ComfyUI-VibeVoice",
                "pip install -r requirements.txt"
            ]
            
            # Execute commands
            for command in commands:
                print(f"Executing: {command}")
                result = ssh.run_commands([command])
                if result and result[0].get('exit_code', 0) != 0:
                    print(f"Command failed: {command}")
                    print(f"Error: {result[0].get('output', 'Unknown error')}")
                    return False
                    
            print("VibeVoice custom node installed successfully.")
            return True
            
        except Exception as e:
            print(f"Error installing VibeVoice nodes: {e}")
            return False
    
    def download_vibeVoice_models(self, instance_id: str) -> bool:
        """
        Downloads the VibeVoice-Large model from HuggingFace.
        
        Args:
            instance_id: The RunPod instance ID
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        if not SSHConnection:
            print("SSHConnection not available. Cannot download VibeVoice models.")
            return False
            
        try:
            # Connect to the pod
            ssh = SSHConnection(instance_id)
            
            # Get HuggingFace token if available
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            token_param = f"--token {hf_token}" if hf_token else ""
            
            # Command to download the model
            command = (
                f"cd /workspace/ComfyUI/models && "
                f"huggingface-cli download microsoft/VibeVoice-Large {token_param} "
                f"--revision main"
            )
            
            print(f"Downloading VibeVoice-Large model...")
            result = ssh.run_commands([command])
            
            if result and result[0].get('exit_code', 0) != 0:
                print(f"Model download failed.")
                print(f"Error: {result[0].get('output', 'Unknown error')}")
                return False
                
            print("VibeVoice-Large model downloaded successfully.")
            return True
            
        except Exception as e:
            print(f"Error downloading VibeVoice models: {e}")
            return False
    
    def configure_vibeVoice_workflow(self, instance_id: str) -> str:
        """
        Configures the VibeVoice workflow.
        
        Args:
            instance_id: The RunPod instance ID
            
        Returns:
            str: Path to the configured workflow or empty string if failed
        """
        if not SSHConnection:
            print("SSHConnection not available. Cannot configure VibeVoice workflow.")
            return ""
            
        try:
            # Connect to the pod
            ssh = SSHConnection(instance_id)
            
            # Create a basic VibeVoice workflow structure
            workflow_content = {
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
                                "slot_index": 0
                            }
                        ],
                        "properties": {
                            "Node name for S&R": "VibeVoiceNode"
                        },
                        "widgets_values": [
                            "",  # Reference audio path
                            "",  # Text input
                            1.0,  # Guidance scale
                            50,   # Inference steps
                            0.8,  # Audio length
                            22050 # Sample rate
                        ]
                    },
                    {
                        "id": 2,
                        "type": "SaveAudio",
                        "pos": [500, 300],
                        "size": [300, 200],
                        "flags": {},
                        "order": 1,
                        "mode": 0,
                        "inputs": [
                            {
                                "name": "audio",
                                "type": "AUDIO",
                                "link": 1
                            }
                        ],
                        "outputs": [],
                        "properties": {
                            "Node name for S&R": "SaveAudio"
                        },
                        "widgets_values": [
                            "vibe_voice_output"
                        ]
                    }
                ],
                "links": [
                    [1, 1, 0, 2, 0, "AUDIO"]
                ],
                "groups": [],
                "config": {},
                "extra": {},
                "version": 0.4
            }
            
            # Save the workflow to the pod
            workflow_json = json.dumps(workflow_content, indent=2)
            workflow_path = "/workspace/ComfyUI/workflows/vibe_voice_basic.json"
            
            # Create the workflows directory if it doesn't exist
            ssh.run_commands(["mkdir -p /workspace/ComfyUI/workflows"])
            
            # Save the workflow file
            ssh.write_file(workflow_path, workflow_json)
            
            print(f"VibeVoice workflow configured at {workflow_path}")
            return workflow_path
            
        except Exception as e:
            print(f"Error configuring VibeVoice workflow: {e}")
            return ""
    
    def validate_vibeVoice_setup(self, instance_id: str) -> ValidationResult:
        """
        Validates that the VibeVoice setup is working correctly.
        
        Args:
            instance_id: The RunPod instance ID
            
        Returns:
            ValidationResult: Validation results
        """
        checks = {}
        errors = []
        warnings = []
        details = {}
        
        if not SSHConnection:
            errors.append("SSHConnection not available. Cannot validate VibeVoice setup.")
            return ValidationResult(
                success=False,
                instance_id=instance_id,
                checks=checks,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now(),
                details=details
            )
            
        try:
            # Connect to the pod
            ssh = SSHConnection(instance_id)
            
            # Check if VibeVoice custom node directory exists
            result = ssh.run_commands(["ls /workspace/ComfyUI/custom_nodes/ComfyUI-VibeVoice"])
            checks["custom_node_exists"] = result and result[0].get('exit_code', 1) == 0
            
            if not checks["custom_node_exists"]:
                errors.append("VibeVoice custom node directory not found")
            
            # Check if VibeVoice model directory exists
            result = ssh.run_commands(["ls /workspace/ComfyUI/models--microsoft--VibeVoice-Large"])
            checks["model_exists"] = result and result[0].get('exit_code', 1) == 0
            
            if not checks["model_exists"]:
                warnings.append("VibeVoice model directory not found (may be downloading)")
            
            # Check if ComfyUI is running
            result = ssh.run_commands(["ps aux | grep comfyui | grep -v grep"])
            checks["comfyui_running"] = result and result[0].get('exit_code', 1) == 0
            
            if not checks["comfyui_running"]:
                errors.append("ComfyUI process not found running")
            
            # Get disk usage
            result = ssh.run_commands(["df -h /workspace"])
            if result and result[0].get('exit_code', 1) == 0:
                details["disk_usage"] = result[0].get('output', '').strip()
            
            # Get memory usage
            result = ssh.run_commands(["free -h"])
            if result and result[0].get('exit_code', 1) == 0:
                details["memory_usage"] = result[0].get('output', '').strip()
            
            success = all(checks.values()) and len(errors) == 0
            
            return ValidationResult(
                success=success,
                instance_id=instance_id,
                checks=checks,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now(),
                details=details
            )
            
        except Exception as e:
            errors.append(f"Error during validation: {e}")
            return ValidationResult(
                success=False,
                instance_id=instance_id,
                checks=checks,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now(),
                details=details
            )

    def test_vibeVoice_workflow(self, instance_id: str, test_text: str = "Hello, this is a test of VibeVoice.",
                                  reference_audio_path: str = None) -> Dict[str, Any]:
        """
        Tests the VibeVoice workflow by sending a sample request to the ComfyUI API.
        
        Args:
            instance_id: The RunPod instance ID
            test_text: Text to synthesize (default: "Hello, this is a test of VibeVoice.")
            reference_audio_path: Path to reference audio file on the pod (optional)
            
        Returns:
            Dict containing test results
        """
        if not SSHConnection:
            return {"success": False, "error": "SSHConnection not available"}
            
        try:
            # Connect to the pod
            ssh = SSHConnection(instance_id)
            
            # Get ComfyUI port (default 8188)
            comfyui_port = os.getenv("COMFYUI_PORT", "8188")
            
            # Create a test workflow
            test_workflow = {
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
                                "slot_index": 0
                            }
                        ],
                        "properties": {
                            "Node name for S&R": "VibeVoiceNode"
                        },
                        "widgets_values": [
                            reference_audio_path or "",  # Reference audio path
                            test_text,  # Text input
                            1.0,  # Guidance scale
                            50,   # Inference steps
                            0.8,  # Audio length
                            22050 # Sample rate
                        ]
                    },
                    {
                        "id": 2,
                        "type": "SaveAudio",
                        "pos": [500, 300],
                        "size": [300, 200],
                        "flags": {},
                        "order": 1,
                        "mode": 0,
                        "inputs": [
                            {
                                "name": "audio",
                                "type": "AUDIO",
                                "link": 1
                            }
                        ],
                        "outputs": [],
                        "properties": {
                            "Node name for S&R": "SaveAudio"
                        },
                        "widgets_values": [
                            "vibe_voice_test_output"
                        ]
                    }
                ],
                "links": [
                    [1, 1, 0, 2, 0, "AUDIO"]
                ],
                "groups": [],
                "config": {},
                "extra": {},
                "version": 0.4
            }
            
            # Save test workflow to pod
            workflow_json = json.dumps(test_workflow, indent=2)
            workflow_path = "/workspace/ComfyUI/workflows/vibe_voice_test.json"
            ssh.write_file(workflow_path, workflow_json)
            
            # Send workflow to ComfyUI API
            curl_command = (
                f"curl -X POST http://localhost:{comfyui_port}/prompt "
                f"-H 'Content-Type: application/json' "
                f"-d '{{\"prompt\": {json.dumps(test_workflow)}}}'"
            )
            
            result = ssh.run_commands([curl_command])
            if result and result[0].get('exit_code', 0) != 0:
                return {"success": False, "error": f"Failed to send workflow: {result[0].get('output', 'Unknown error')}"}
                
            # Parse response
            try:
                response_data = json.loads(result[0].get('output', '{}'))
                prompt_id = response_data.get('prompt_id')
                if not prompt_id:
                    return {"success": False, "error": "No prompt_id returned from ComfyUI"}
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid JSON response from ComfyUI"}
                
            # Wait for workflow completion (with timeout)
            max_wait_time = 120  # 2 minutes
            check_interval = 5
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                history_command = f"curl -s http://localhost:{comfyui_port}/history"
                history_result = ssh.run_commands([history_command])
                
                if history_result and history_result[0].get('exit_code', 0) == 0:
                    try:
                        history_data = json.loads(history_result[0].get('output', '{}'))
                        if prompt_id in history_data and history_data[prompt_id].get('status', {}).get('completed', False):
                            # Workflow completed successfully
                            outputs = history_data[prompt_id].get('outputs', {})
                            
                            # Check if output files were generated
                            output_files = []
                            for node_id, output_data in outputs.items():
                                if 'audio' in output_data:
                                    output_files.extend(output_data['audio'])
                            
                            return {
                                "success": True,
                                "prompt_id": prompt_id,
                                "outputs": output_files,
                                "message": f"Workflow completed successfully with {len(output_files)} output files"
                            }
                    except json.JSONDecodeError:
                        pass
                
                time.sleep(check_interval)
                
            return {"success": False, "error": "Workflow execution timed out"}
                
        except Exception as e:
            return {"success": False, "error": f"Error testing workflow: {e}"}
    
    def validate_audio_output(self, instance_id: str, output_file_path: str) -> Dict[str, Any]:
        """
        Validates generated audio output by checking file properties.
        
        Args:
            instance_id: The RunPod instance ID
            output_file_path: Path to the generated audio file on the pod
            
        Returns:
            Dict containing validation results
        """
        if not SSHConnection:
            return {"success": False, "error": "SSHConnection not available"}
            
        try:
            # Connect to the pod
            ssh = SSHConnection(instance_id)
            
            # Check if file exists
            check_command = f"test -f {output_file_path} && echo 'exists' || echo 'missing'"
            result = ssh.run_commands([check_command])
            
            if result and result[0].get('output', '').strip() == 'missing':
                return {"success": False, "error": f"Audio file not found: {output_file_path}"}
                
            # Get file size
            size_command = f"stat -c %s {output_file_path}"
            size_result = ssh.run_commands([size_command])
            file_size = int(size_result[0].get('output', '0').strip()) if size_result and size_result[0].get('exit_code', 1) == 0 else 0
            
            # Get file type
            type_command = f"file -b {output_file_path}"
            type_result = ssh.run_commands([type_command])
            file_type = type_result[0].get('output', '').strip() if type_result and type_result[0].get('exit_code', 1) == 0 else "Unknown"
            
            # Basic validation
            is_valid = file_size > 0 and ('audio' in file_type.lower() or file_type == "Unknown")
            
            return {
                "success": is_valid,
                "file_size": file_size,
                "file_type": file_type,
                "message": "Audio file validation passed" if is_valid else "Audio file validation failed"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error validating audio output: {e}"}
    
    def run_comprehensive_test(self, instance_id: str, test_text: str = "Hello, this is a comprehensive test of VibeVoice.") -> Dict[str, Any]:
        """
        Runs a comprehensive test of the VibeVoice setup including workflow execution and output validation.
        
        Args:
            instance_id: The RunPod instance ID
            test_text: Text to synthesize for testing
            
        Returns:
            Dict containing comprehensive test results
        """
        results = {
            "setup_validation": None,
            "workflow_test": None,
            "audio_validation": None,
            "overall_success": False,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Step 1: Validate setup
            print("1. Validating VibeVoice setup...")
            setup_result = self.validate_vibeVoice_setup(instance_id)
            results["setup_validation"] = {
                "success": setup_result.success,
                "checks": setup_result.checks,
                "errors": setup_result.errors,
                "warnings": setup_result.warnings
            }
            
            if not setup_result.success:
                results["message"] = "Setup validation failed"
                return results
                
            # Step 2: Test workflow execution
            print("2. Testing VibeVoice workflow execution...")
            workflow_result = self.test_vibeVoice_workflow(instance_id, test_text)
            results["workflow_test"] = workflow_result
            
            if not workflow_result.get("success", False):
                results["message"] = "Workflow execution test failed"
                return results
                
            # Step 3: Validate audio output
            print("3. Validating generated audio output...")
            output_files = workflow_result.get("outputs", [])
            if output_files:
                # Validate the first output file
                first_output = output_files[0]
                audio_result = self.validate_audio_output(instance_id, first_output.get("filename", "") if isinstance(first_output, dict) else first_output)
                results["audio_validation"] = audio_result
                
                if not audio_result.get("success", False):
                    results["message"] = "Audio output validation failed"
                    return results
            else:
                results["audio_validation"] = {"success": False, "error": "No output files generated"}
                results["message"] = "No output files generated for validation"
                return results
                
            # All tests passed
            results["overall_success"] = True
            results["message"] = "Comprehensive test completed successfully"
            
        except Exception as e:
            results["error"] = f"Error during comprehensive test: {e}"
            results["message"] = "Comprehensive test failed due to exception"
            
        return results


# Example usage
if __name__ == "__main__":
    # Example of how to use the VibeVoiceManager
    try:
        manager = VibeVoiceManager()
        print("VibeVoiceManager initialized successfully.")
    except Exception as e:
        print(f"Error initializing VibeVoiceManager: {e}")