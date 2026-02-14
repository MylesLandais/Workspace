"""
WD14 ONNX-based image tagger for character and general tag extraction.
Separate from CLIP tagging system - runs independently with 95% confidence filtering.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from PIL import Image
import onnxruntime as ort
from huggingface_hub import hf_hub_download

from .models import WD14Result, WD14Tag, WD14TagCategory
from .config import WD14Config


class WD14Tagger:
    """ONNX-based WD14 image tagger with automatic model download."""

    TAG_CATEGORIES = {
        "9b": WD14TagCategory.GENERAL,
        "9b_e": WD14TagCategory.GENERAL,
    }

    def __init__(self, config: Optional[WD14Config] = None):
        """Initialize WD14 tagger with ONNX model.

        Args:
            config: WD14Config instance or uses defaults

        Raises:
            RuntimeError: If ONNX model cannot be loaded
        """
        self.config = config or WD14Config()
        self.session = None
        self.model_version = "wd14-vit"
        self.tags_list = None
        self._init_model()

    def _init_model(self):
        """Initialize ONNX runtime session with WD14 model."""
        try:
            # Download model from HuggingFace if not cached
            model_path = self._get_or_download_model()

            # Create ONNX session with GPU/CPU providers
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session_options.log_severity_level = 2  # Warning level

            self.session = ort.InferenceSession(
                str(model_path),
                sess_options=session_options,
                providers=self.config.providers,
            )

            # Load tag list from model directory
            self._load_tags()

        except Exception as e:
            raise RuntimeError(f"Failed to initialize WD14 ONNX model: {e}")

    def _get_or_download_model(self) -> Path:
        """Get model path, downloading if needed."""
        cache_dir = self.config.model_cache_dir or Path.home() / ".cache" / "wd14_models"
        repo_dir = cache_dir / self.config.model_repo.replace("/", "_")
        repo_dir.mkdir(parents=True, exist_ok=True)

        model_filename = "model.onnx"
        model_path = repo_dir / model_filename

        if not model_path.exists():
            # Download model from HuggingFace
            local_path = hf_hub_download(
                repo_id=self.config.model_repo,
                filename=model_filename,
                cache_dir=repo_dir.parent.parent,  # Let hf_hub_download manage caching
            )
            # Copy to our target location if different
            if local_path != str(model_path):
                import shutil
                shutil.copy(local_path, model_path)

        return model_path

    def _load_tags(self):
        """Load tag labels from model repo."""
        try:
            tags_dir = Path.home() / ".cache" / "wd14_models" / self.config.model_repo.replace("/", "_")
            tags_dir.mkdir(parents=True, exist_ok=True)
            csv_path = tags_dir / "selected_tags.csv"

            if not csv_path.exists():
                # Download tags CSV from HuggingFace
                local_path = hf_hub_download(
                    repo_id=self.config.model_repo,
                    filename="selected_tags.csv",
                    cache_dir=tags_dir.parent.parent,
                )
                # Copy to target location if different
                if local_path != str(csv_path):
                    import shutil
                    shutil.copy(local_path, csv_path)

            # Parse CSV to extract tag names
            self.tags_list = []
            with open(csv_path, "r", encoding="utf-8") as f:
                # Skip header: index,name,category,count
                next(f)
                for line in f:
                    parts = line.strip().split(",", 3)
                    if len(parts) >= 2:
                        self.tags_list.append(parts[1])

        except Exception as e:
            raise RuntimeError(f"Failed to load WD14 tags: {e}")

    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for WD14 ONNX model.

        Args:
            image: PIL Image

        Returns:
            Preprocessed image array (1, 3, 448, 448)
        """
        # Resize to 448x448 (standard for WD14)
        image = image.convert("RGB")
        image = image.resize((448, 448), Image.LANCZOS)

        # Convert to numpy array and normalize
        image_array = np.array(image, dtype=np.float32)
        image_array = image_array / 255.0

        # Normalize with ImageNet mean/std
        mean = np.array([0.48145466, 0.4578275, 0.40821073])
        std = np.array([0.26862954, 0.26130258, 0.27577711])
        image_array = (image_array - mean) / std

        # Add batch dimension and transpose to (1, 3, 448, 448)
        image_array = np.transpose(image_array, (2, 0, 1))
        image_array = np.expand_dims(image_array, 0)

        return image_array

    def tag_image(self, image: Image.Image, image_sha256: Optional[str] = None) -> WD14Result:
        """Tag a single image using WD14 ONNX model.

        Args:
            image: PIL Image to tag
            image_sha256: Optional SHA256 hash of image (computed if not provided)

        Returns:
            WD14Result with tags filtered by 95% confidence threshold
        """
        if not self.session or not self.tags_list:
            raise RuntimeError("WD14 model not initialized")

        # Compute SHA256 if not provided
        if not image_sha256:
            image_bytes = image.tobytes()
            image_sha256 = hashlib.sha256(image_bytes).hexdigest()

        # Preprocess image
        input_array = self._preprocess_image(image)

        # Run inference
        input_name = self.session.get_inputs()[0].name
        output_names = [o.name for o in self.session.get_outputs()]

        outputs = self.session.run(output_names, {input_name: input_array})

        # Parse outputs: [logits, last_hidden_state] or just [logits]
        logits = outputs[0][0]  # First output, first batch item

        # Convert logits to probabilities using sigmoid
        scores = 1.0 / (1.0 + np.exp(-logits))

        # Create result
        result = WD14Result(
            image_sha256=image_sha256,
            character_tags=[],
            general_tags=[],
            rating="safe",
            model_version=self.model_version,
            score_metadata={},
        )

        # Filter tags by confidence threshold
        threshold = self.config.confidence_threshold
        rating_tag = None

        for tag_name, score in zip(self.tags_list, scores):
            if score < threshold:
                continue

            # Store raw score
            result.score_metadata[tag_name] = float(score)

            # Categorize tag
            if tag_name in ("safe", "questionable", "explicit"):
                # Rating tag - keep highest confidence
                if rating_tag is None or score > rating_tag[1]:
                    rating_tag = (tag_name, score)
            else:
                # Determine category (simplified: assume general, could be enhanced)
                category = WD14TagCategory.GENERAL
                tag = WD14Tag(name=tag_name, category=category, confidence=float(score))
                result.general_tags.append(tag)

        # Set rating if found
        if rating_tag:
            result.rating = rating_tag[0]

        # Sort by confidence (descending)
        result.character_tags.sort(key=lambda t: t.confidence, reverse=True)
        result.general_tags.sort(key=lambda t: t.confidence, reverse=True)

        return result

    def tag_images_batch(self, images: List[Tuple[Image.Image, Optional[str]]]) -> List[WD14Result]:
        """Tag multiple images (list of tuples with image and optional SHA256).

        Args:
            images: List of (PIL Image, optional SHA256) tuples

        Returns:
            List of WD14Result objects
        """
        return [self.tag_image(img, sha256) for img, sha256 in images]

    def load_and_tag(self, image_path: Path, image_sha256: Optional[str] = None) -> WD14Result:
        """Load image from file and tag it.

        Args:
            image_path: Path to image file
            image_sha256: Optional SHA256 (computed from file if not provided)

        Returns:
            WD14Result with tags
        """
        image = Image.open(image_path)
        return self.tag_image(image, image_sha256)
