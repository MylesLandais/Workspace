"""
ComfyUI Workspace Management

Provides utilities for organizing ComfyUI projects with structured directories
for workflows, reference audio, outputs, and templates.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class WorkspaceManager:
    """Manages ComfyUI project workspace structure and organization."""
    
    def __init__(self, base_path: str = "comfyui_projects"):
        """Initialize workspace manager with base directory path."""
        self.base_path = Path(base_path)
        self.workflows_path = self.base_path / "workflows"
        self.reference_audio_path = self.base_path / "reference_audio"
        self.outputs_path = self.base_path / "outputs"
        self.templates_path = self.base_path / "templates"
    
    def initialize_workspace(self, project_name: Optional[str] = None) -> Path:
        """
        Initialize workspace directory structure.
        
        Args:
            project_name: Optional project name for scoped workspace
            
        Returns:
            Path to the initialized workspace
        """
        if project_name:
            workspace_path = self.base_path / project_name
        else:
            workspace_path = self.base_path
            
        # Create main directories
        directories = [
            workspace_path / "workflows",
            workspace_path / "reference_audio" / "samples",
            workspace_path / "outputs",
            workspace_path / "templates"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Create metadata files
        self._create_workspace_metadata(workspace_path)
        
        return workspace_path
    
    def get_workflow_path(self, workflow_name: str, project_name: Optional[str] = None) -> Path:
        """Get path for a specific workflow directory."""
        if project_name:
            return self.base_path / project_name / "workflows" / workflow_name
        return self.workflows_path / workflow_name
    
    def get_reference_audio_path(self, audio_name: str, project_name: Optional[str] = None) -> Path:
        """Get path for a specific reference audio file."""
        if project_name:
            return self.base_path / project_name / "reference_audio" / audio_name
        return self.reference_audio_path / audio_name
    
    def get_outputs_path(self, session_id: str, project_name: Optional[str] = None) -> Path:
        """Get path for a specific output session directory."""
        if project_name:
            outputs_base = self.base_path / project_name / "outputs"
        else:
            outputs_base = self.outputs_path
            
        session_path = outputs_base / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (session_path / "generated").mkdir(exist_ok=True)
        (session_path / "logs").mkdir(exist_ok=True)
        
        return session_path
    
    def get_template_path(self, template_name: str, project_name: Optional[str] = None) -> Path:
        """Get path for a specific template directory."""
        if project_name:
            return self.base_path / project_name / "templates" / template_name
        return self.templates_path / template_name
    
    def create_workflow_structure(self, workflow_name: str, project_name: Optional[str] = None) -> Path:
        """
        Create a complete workflow directory structure with metadata files.
        
        Args:
            workflow_name: Name of the workflow
            project_name: Optional project scope
            
        Returns:
            Path to the created workflow directory
        """
        workflow_path = self.get_workflow_path(workflow_name, project_name)
        workflow_path.mkdir(parents=True, exist_ok=True)
        
        # Create workflow metadata template
        metadata = {
            "name": workflow_name,
            "version": "1.0.0",
            "description": f"ComfyUI workflow: {workflow_name}",
            "created_at": datetime.now().isoformat(),
            "comfyui_version": ">=1.0.0",
            "custom_nodes": [],
            "models": [],
            "requirements": {
                "gpu_memory": "8GB",
                "python_packages": []
            }
        }
        
        metadata_file = workflow_path / "metadata.yaml"
        with open(metadata_file, 'w') as f:
            import yaml
            yaml.dump(metadata, f, default_flow_style=False)
        
        # Create placeholder files
        (workflow_path / "workflow.json").touch()
        (workflow_path / "requirements.txt").touch()
        
        return workflow_path
    
    def list_workflows(self, project_name: Optional[str] = None) -> list:
        """List all available workflows in the workspace."""
        if project_name:
            workflows_dir = self.base_path / project_name / "workflows"
        else:
            workflows_dir = self.workflows_path
            
        if not workflows_dir.exists():
            return []
            
        workflows = []
        for item in workflows_dir.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.yaml"
                if metadata_file.exists():
                    try:
                        import yaml
                        with open(metadata_file, 'r') as f:
                            metadata = yaml.safe_load(f)
                        workflows.append({
                            "name": item.name,
                            "path": str(item),
                            "metadata": metadata
                        })
                    except Exception:
                        workflows.append({
                            "name": item.name,
                            "path": str(item),
                            "metadata": None
                        })
        
        return workflows
    
    def get_session_id(self) -> str:
        """Generate a unique session ID for outputs."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _create_workspace_metadata(self, workspace_path: Path) -> None:
        """Create workspace metadata and configuration files."""
        metadata = {
            "workspace_version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "structure": {
                "workflows": "ComfyUI workflow definitions and metadata",
                "reference_audio": "Reference audio files for voice-based workflows",
                "outputs": "Generated content organized by session",
                "templates": "Custom Docker templates and build configurations"
            }
        }
        
        metadata_file = workspace_path / "workspace.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create reference audio metadata
        audio_metadata = {
            "samples": {},
            "metadata_version": "1.0.0",
            "created_at": datetime.now().isoformat()
        }
        
        audio_metadata_file = workspace_path / "reference_audio" / "metadata.json"
        with open(audio_metadata_file, 'w') as f:
            json.dump(audio_metadata, f, indent=2)


# Configuration management
class ComfyConfig:
    """Manages ComfyUI infrastructure configuration settings."""
    
    def __init__(self, config_file: str = "comfy_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        default_config = {
            "runpod": {
                "default_gpu": "RTX_5090",
                "default_disk_size": 50,
                "auto_shutdown_minutes": 60
            },
            "templates": {
                "base_image": "ubuntu:22.04",
                "cuda_version": "12.1.1",
                "python_version": "3.10"
            },
            "workflows": {
                "default_timeout": 300,
                "max_retries": 3
            },
            "monitoring": {
                "enabled": True,
                "metrics_interval": 60
            }
        }
        
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file."""
        config_to_save = config or self.config
        with open(self.config_file, 'w') as f:
            json.dump(config_to_save, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot notation key."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()


if __name__ == "__main__":
    # Example usage
    workspace = WorkspaceManager()
    
    # Initialize workspace
    workspace_path = workspace.initialize_workspace()
    print(f"Initialized workspace at: {workspace_path}")
    
    # Create a sample workflow
    vibeVoice_path = workspace.create_workflow_structure("vibeVoice")
    print(f"Created VibeVoice workflow at: {vibeVoice_path}")
    
    # List workflows
    workflows = workspace.list_workflows()
    print(f"Available workflows: {[w['name'] for w in workflows]}")
    
    # Create session output directory
    session_id = workspace.get_session_id()
    output_path = workspace.get_outputs_path(session_id)
    print(f"Created output session: {output_path}")