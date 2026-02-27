"""
Batch Processor for ComfyUI Metadata Analysis

Processes directories of PNG images, extracts metadata, and performs
classification and decomposition analysis.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

from .extractor import MetadataExtractor
from .parser import MetadataParser
from .classifier import CharacterClassifier
from .decomposer import PromptDecomposer


class BatchProcessor:
    """Processes batches of ComfyUI images for metadata analysis."""

    def __init__(
        self,
        classify_characters: bool = True,
        decompose_prompts: bool = True,
        shay_md_path: Optional[Path] = None,
        lexie_md_path: Optional[Path] = None
    ):
        """
        Initialize the batch processor.

        Args:
            classify_characters: Whether to perform character classification
            decompose_prompts: Whether to decompose prompts into components
            shay_md_path: Path to Subject-Shay.md (default: data/Prompts/Subject-Shay.md)
            lexie_md_path: Path to Subject-Lexie.md (default: data/Prompts/Subject-Lexie.md)
        """
        self.extractor = MetadataExtractor()
        self.parser = MetadataParser()
        
        self.classify_characters = classify_characters
        self.decompose_prompts = decompose_prompts
        
        self.classifier = None
        self.decomposer = None
        
        if classify_characters:
            # Disable semantic similarity by default - it requires network access
            # Rule-based classification works fine without network
            self.classifier = CharacterClassifier(use_semantic=False)
            if shay_md_path is None:
                shay_md_path = Path("data/Prompts/Subject-Shay.md")
            if lexie_md_path is None:
                lexie_md_path = Path("data/Prompts/Subject-Lexie.md")
            self.classifier.load_character_descriptors(shay_md_path, lexie_md_path)
        
        if decompose_prompts:
            self.decomposer = PromptDecomposer()

    def process_directory(
        self,
        directory_path: Path,
        recursive: bool = False,
        pattern: str = "*.png"
    ) -> pd.DataFrame:
        """
        Process all PNG files in a directory.

        Args:
            directory_path: Directory to process
            recursive: Whether to process subdirectories
            pattern: File pattern to match (default: "*.png")

        Returns:
            DataFrame with extracted and analyzed metadata
        """
        directory_path = Path(directory_path)
        
        # Extract metadata from all images
        extracted_data = self.extractor.extract_from_directory(
            directory_path,
            recursive=recursive,
            pattern=pattern
        )
        
        if not extracted_data:
            # Return empty DataFrame with expected columns
            return self._create_empty_dataframe()
        
        # Parse metadata into structured format
        flattened_data = []
        for item in extracted_data:
            flattened = self.parser.flatten_metadata(item)
            flattened_data.append(flattened)
        
        # Create DataFrame
        df = pd.DataFrame(flattened_data)
        
        # Perform classification if enabled
        if self.classify_characters and self.classifier and 'positive_prompt' in df.columns:
            df['character_cluster'] = df['positive_prompt'].apply(
                self.classifier.classify_character
            )
        else:
            df['character_cluster'] = 'universal'
        
        # Perform decomposition if enabled
        if self.decompose_prompts and self.decomposer and 'positive_prompt' in df.columns:
            decomposition_results = []
            for idx, row in df.iterrows():
                prompt = row.get('positive_prompt', '')
                cluster = row.get('character_cluster', 'universal')
                decomposed = self.decomposer.decompose_prompt(prompt, cluster)
                decomposition_results.append(decomposed)
            
            # Add decomposition columns
            for key in ['core_subject', 'action_pose', 'template', 'style_modifiers', 'technical_tokens']:
                df[key] = [r[key] for r in decomposition_results]
        
        return df

    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create an empty DataFrame with expected columns."""
        columns = [
            'filename', 'filepath', 'positive_prompt', 'negative_prompt',
            'model_name', 'seed', 'cfg', 'steps', 'sampler_name', 'scheduler',
            'width', 'height', 'character_cluster'
        ]
        
        if self.decompose_prompts:
            columns.extend([
                'core_subject', 'action_pose', 'template', 'style_modifiers', 'technical_tokens'
            ])
        
        return pd.DataFrame(columns=columns)

    def process_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Process a single PNG file.

        Args:
            file_path: Path to PNG file

        Returns:
            DataFrame with single row of metadata, or None if processing fails
        """
        file_path = Path(file_path)
        
        # Extract metadata
        extracted_data = self.extractor.extract_from_image(file_path)
        if not extracted_data:
            return None
        
        # Parse metadata
        flattened = self.parser.flatten_metadata(extracted_data)
        
        # Create DataFrame
        df = pd.DataFrame([flattened])
        
        # Perform classification if enabled
        if self.classify_characters and self.classifier and 'positive_prompt' in df.columns:
            df['character_cluster'] = df['positive_prompt'].apply(
                self.classifier.classify_character
            )
        else:
            df['character_cluster'] = 'universal'
        
        # Perform decomposition if enabled
        if self.decompose_prompts and self.decomposer and 'positive_prompt' in df.columns:
            for idx, row in df.iterrows():
                prompt = row.get('positive_prompt', '')
                cluster = row.get('character_cluster', 'universal')
                decomposed = self.decomposer.decompose_prompt(prompt, cluster)
                for key, value in decomposed.items():
                    df.at[idx, key] = value
        
        return df

