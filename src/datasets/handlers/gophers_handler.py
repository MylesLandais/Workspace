"""
Dataset handler for the Go Gophers dataset from Hugging Face.
"""
from pathlib import Path
from src.datasets.base_handler import BaseDatasetHandler

# Try to import the datasets library, but don't fail if it's not installed
# The user will be prompted to install it if they try to use this handler.
try:
    from datasets import load_dataset, DatasetDict
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    DatasetDict = None

class GophersHandler(BaseDatasetHandler):
    """
    Manages the landam/gogophers dataset from the Hugging Face Hub.
    """

    REPO_ID = "landam/gogophers"

    @property
    def name(self) -> str:
        return "gophers"

    def info(self) -> dict:
        return {
            "name": "Go Gophers",
            "description": "A fun, professional art style dataset for developers, used for training diffusion and vision models.",
            "source_url": f"https://huggingface.co/datasets/{self.REPO_ID}",
            "content_type": "image-caption",
        }

    def get(self, destination: Path = Path("datasets")) -> Path:
        """
        Ensures the Go Gophers dataset is available locally by downloading it
        from the Hugging Face Hub.

        Args:
            destination (Path): The root directory where datasets should be stored.

        Returns:
            Path: The path to the local dataset directory.
        """
        if not HAS_DATASETS:
            raise ImportError("The 'datasets' library is required to use the Gophers dataset. Please install it with: pip install datasets")

        dataset_dir = destination / self.name
        self._ensure_dir(dataset_dir)

        print(f"Loading '{self.name}' dataset from Hugging Face Hub...")
        print(f"This may take a while the first time...")

        try:
            # Download and save the dataset to the specified directory
            dataset: DatasetDict = load_dataset(self.REPO_ID, cache_dir=str(dataset_dir / "cache"))

            # The 'datasets' library handles all the caching, so we just
            # need to confirm it's there. We can save a local copy for inspection.
            # For simplicity, we'll just point to the cache dir.
            print(f"✅ Successfully loaded '{self.name}' dataset.")
            print(f"   Local cache: {dataset_dir / 'cache'}")
            print(f"   Splits: {list(dataset.keys())}")
            print(f"   Features: {dataset['train'].features}")

            return dataset_dir

        except Exception as e:
            print(f"❌ Failed to download '{self.name}' dataset: {e}")
            print(f"   Please check your internet connection and Hugging Face authentication.")
            raise
