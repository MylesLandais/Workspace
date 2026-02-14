"""
HuggingFace model downloader utility for automated setup.

Automates model discovery, verification, and download from HuggingFace Hub.
Supports ASR models with dependency checking and caching.
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from huggingface_hub import (
    snapshot_download,
    login,
    whoami,
    HfApi,
    model_info
)


@dataclass
class ModelManifest:
    """Manifest entry for a downloaded model."""
    model_id: str
    local_path: str
    download_timestamp: datetime
    size_bytes: int
    checksum: str
    dependencies: List[str]
    verified: bool = False


class HuggingFaceModelDownloader:
    """
    Automated HuggingFace model downloader with manifest tracking.

    Features:
    - Automatic model discovery and metadata retrieval
    - Dependency checking and installation
    - Checksum verification
    - Persistent manifest tracking
    - Progress reporting
    """

    DEFAULT_CACHE_DIR = Path.home() / ".cache" / "huggingface"
    MANIFEST_FILE = Path("models_manifest.json")

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        hf_token: Optional[str] = None,
        verify_checksums: bool = True
    ):
        """
        Initialize model downloader.

        Args:
            cache_dir: Custom cache directory for models
            hf_token: HuggingFace API token (for private models)
            verify_checksums: Verify model checksums after download
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.hf_token = hf_token
        self.verify_checksums = verify_checksums
        self.api = HfApi(token=hf_token)

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load manifest
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, ModelManifest]:
        """Load model manifest from disk."""
        if self.MANIFEST_FILE.exists():
            try:
                with open(self.MANIFEST_FILE, 'r') as f:
                    data = json.load(f)
                    return {
                        model_id: ModelManifest(**entry)
                        for model_id, entry in data.items()
                    }
            except Exception as e:
                print(f"⚠️  Warning: Failed to load manifest: {e}")
        return {}

    def _save_manifest(self):
        """Save model manifest to disk."""
        try:
            data = {
                model_id: {
                    "model_id": entry.model_id,
                    "local_path": entry.local_path,
                    "download_timestamp": entry.download_timestamp.isoformat(),
                    "size_bytes": entry.size_bytes,
                    "checksum": entry.checksum,
                    "dependencies": entry.dependencies,
                    "verified": entry.verified
                }
                for model_id, entry in self.manifest.items()
            }
            with open(self.MANIFEST_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Failed to save manifest: {e}")

    def login_hf(self, token: Optional[str] = None) -> bool:
        """
        Login to HuggingFace Hub.

        Args:
            token: HuggingFace API token (uses self.hf_token if None)

        Returns:
            True if login successful, False otherwise
        """
        try:
            token = token or self.hf_token or os.environ.get("HF_TOKEN")
            if not token:
                print("❌ No HF token provided. Using public access only.")
                return False

            login(token=token)
            user_info = whoami()
            print(f"✅ Logged in as: {user_info}")
            return True

        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False

    def get_model_metadata(self, model_id: str) -> Dict:
        """
        Retrieve model metadata from HuggingFace Hub.

        Args:
            model_id: Model ID (e.g., "nvidia/parakeet-tdt-0.6b-v2")

        Returns:
            Dictionary with model metadata
        """
        try:
            info = self.api.model_info(repo_id=model_id)
            return {
                "model_id": model_id,
                "author": info.author,
                "tags": info.tags,
                "downloads": info.downloads,
                "likes": info.likes,
                "created_at": info.created_at.isoformat(),
                "last_modified": info.last_modified.isoformat(),
                "model_size_bytes": info.safetensors.get("total", 0),
                "pipeline_tag": info.pipeline_tag,
                "private": info.private
            }
        except Exception as e:
            raise RuntimeError(f"Failed to fetch model metadata: {e}") from e

    def check_dependencies(self, model_metadata: Dict) -> Tuple[List[str], List[str]]:
        """
        Check if required dependencies are installed.

        Args:
            model_metadata: Model metadata from HuggingFace

        Returns:
            Tuple of (installed_deps, missing_deps)
        """
        pipeline_tag = model_metadata.get("pipeline_tag", "")
        tags = model_metadata.get("tags", [])

        # Map pipeline tags to dependencies
        dependency_map = {
            "automatic-speech-recognition": ["transformers", "torch", "torchaudio"],
            "audio-to-audio": ["transformers", "torch", "torchaudio"],
            "text-to-speech": ["transformers", "torch"],
            "feature-extraction": ["transformers", "torch"]
        }

        required_deps = set()
        if pipeline_tag in dependency_map:
            required_deps.update(dependency_map[pipeline_tag])

        # Check additional tags for specific requirements
        if any("transformers" in tag for tag in tags):
            required_deps.add("transformers")
        if any("pytorch" in tag for tag in tags):
            required_deps.add("torch")

        # Check which are installed
        installed = []
        missing = []

        for dep in required_deps:
            try:
                __import__(dep)
                installed.append(dep)
            except ImportError:
                missing.append(dep)

        return installed, missing

    def download_model(
        self,
        model_id: str,
        force_redownload: bool = False,
        progress: bool = True
    ) -> Path:
        """
        Download model from HuggingFace Hub.

        Args:
            model_id: Model ID (e.g., "nvidia/parakeet-tdt-0.6b-v2")
            force_redownload: Force download even if model exists
            progress: Show download progress

        Returns:
            Path to downloaded model
        """
        # Check if already downloaded
        if not force_redownload and model_id in self.manifest:
            manifest_entry = self.manifest[model_id]
            if Path(manifest_entry.local_path).exists():
                print(f"✅ Model already downloaded: {model_id}")
                return Path(manifest_entry.local_path)

        # Get model metadata
        print(f"📦 Fetching metadata for: {model_id}")
        metadata = self.get_model_metadata(model_id)

        # Check dependencies
        installed, missing = self.check_dependencies(metadata)
        if missing:
            print(f"⚠️  Missing dependencies: {', '.join(missing)}")
            print(f"💡 Install with: pip install {' '.join(missing)}")
            # Continue anyway - let user handle dependencies

        # Download model
        print(f"⬇️  Downloading model: {model_id}")
        try:
            local_path = snapshot_download(
                repo_id=model_id,
                cache_dir=self.cache_dir,
                local_dir=self.cache_dir / model_id.replace("/", "--"),
                local_dir_use_symlinks=False,
                progress=progress
            )

            # Calculate checksum
            checksum = self._calculate_checksum(local_path)

            # Get size
            size_bytes = sum(
                f.stat().st_size
                for f in Path(local_path).rglob("*")
                if f.is_file()
            )

            # Update manifest
            self.manifest[model_id] = ModelManifest(
                model_id=model_id,
                local_path=str(local_path),
                download_timestamp=datetime.now(),
                size_bytes=size_bytes,
                checksum=checksum,
                dependencies=installed,
                verified=False
            )
            self._save_manifest()

            print(f"✅ Model downloaded: {model_id}")
            print(f"   Path: {local_path}")
            print(f"   Size: {size_bytes / (1024*1024):.1f} MB")
            print(f"   Checksum: {checksum[:16]}...")

            return Path(local_path)

        except Exception as e:
            raise RuntimeError(f"Failed to download model: {e}") from e

    def _calculate_checksum(self, path: Path) -> str:
        """Calculate SHA256 checksum of model directory."""
        sha256 = hashlib.sha256()
        for file in sorted(path.rglob("*")):
            if file.is_file():
                with open(file, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256.update(chunk)
        return sha256.hexdigest()

    def verify_model(self, model_id: str) -> bool:
        """
        Verify downloaded model integrity.

        Args:
            model_id: Model ID to verify

        Returns:
            True if verified, False otherwise
        """
        if model_id not in self.manifest:
            print(f"❌ Model not in manifest: {model_id}")
            return False

        manifest_entry = self.manifest[model_id]
        local_path = Path(manifest_entry.local_path)

        if not local_path.exists():
            print(f"❌ Model path not found: {local_path}")
            return False

        # Recalculate checksum
        current_checksum = self._calculate_checksum(local_path)

        if current_checksum != manifest_entry.checksum:
            print(f"❌ Checksum mismatch for: {model_id}")
            return False

        # Update manifest
        self.manifest[model_id].verified = True
        self._save_manifest()

        print(f"✅ Model verified: {model_id}")
        return True

    def list_downloaded_models(self) -> List[Dict]:
        """
        List all downloaded models.

        Returns:
            List of model info dictionaries
        """
        return [
            {
                "model_id": entry.model_id,
                "path": entry.local_path,
                "downloaded": entry.download_timestamp,
                "size_mb": entry.size_bytes / (1024*1024),
                "checksum": entry.checksum[:16] + "...",
                "verified": entry.verified,
                "dependencies": entry.dependencies
            }
            for model_id, entry in self.manifest.items()
        ]

    def delete_model(self, model_id: str) -> bool:
        """
        Delete downloaded model.

        Args:
            model_id: Model ID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        if model_id not in self.manifest:
            print(f"❌ Model not in manifest: {model_id}")
            return False

        manifest_entry = self.manifest[model_id]
        local_path = Path(manifest_entry.local_path)

        try:
            # Remove model files
            import shutil
            shutil.rmtree(local_path)

            # Remove from manifest
            del self.manifest[model_id]
            self._save_manifest()

            print(f"✅ Model deleted: {model_id}")
            return True

        except Exception as e:
            print(f"❌ Failed to delete model: {e}")
            return False

    def download_asr_models(
        self,
        model_list: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """
        Download recommended ASR models for evaluation.

        Args:
            model_list: List of model IDs to download (uses defaults if None)

        Returns:
            Dictionary mapping model IDs to local paths
        """
        # Default ASR models for evaluation
        default_models = [
            "nvidia/parakeet-tdt-0.6b-v2",
            "nvidia/canary-qwen-2.5b",
            "openai/whisper-large-v3",
            "allenai/OLMoASR-large.en-v2"
        ]

        models = model_list or default_models

        results = {}

        for model_id in models:
            try:
                print(f"\n{'='*60}")
                local_path = self.download_model(model_id)
                results[model_id] = local_path
            except Exception as e:
                print(f"❌ Failed to download {model_id}: {e}")
                continue

        return results


def main():
    """CLI entry point for model downloader."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download and manage ASR models from HuggingFace"
    )
    parser.add_argument(
        "--download",
        nargs="+",
        help="Model IDs to download"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List downloaded models"
    )
    parser.add_argument(
        "--verify",
        help="Verify a specific model"
    )
    parser.add_argument(
        "--delete",
        help="Delete a specific model"
    )
    parser.add_argument(
        "--token",
        help="HuggingFace API token"
    )
    parser.add_argument(
        "--asr-defaults",
        action="store_true",
        help="Download default ASR evaluation models"
    )

    args = parser.parse_args()

    downloader = HuggingFaceModelDownloader(hf_token=args.token)

    if args.download:
        for model_id in args.download:
            try:
                downloader.download_model(model_id)
            except Exception as e:
                print(f"❌ Error: {e}")

    elif args.asr_defaults:
        downloader.download_asr_models()

    elif args.list:
        models = downloader.list_downloaded_models()
        print("\n📦 Downloaded Models:")
        print("="*60)
        for model in models:
            verified = "✅" if model["verified"] else "❌"
            print(f"{verified} {model['model_id']}")
            print(f"   Path: {model['path']}")
            print(f"   Size: {model['size_mb']:.1f} MB")
            print(f"   Downloaded: {model['downloaded']}")
            print()

    elif args.verify:
        downloader.verify_model(args.verify)

    elif args.delete:
        downloader.delete_model(args.delete)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
