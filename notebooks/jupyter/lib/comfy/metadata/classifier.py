"""
Character Classifier for ComfyUI Prompts

Classifies prompts into character-specific clusters (Shay, Lexie, Universal)
using hybrid rule-based and semantic similarity approaches.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
import warnings

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    warnings.warn("sentence-transformers not available. Semantic similarity will be disabled.")


class CharacterClassifier:
    """Classifies prompts into character clusters using hybrid approach."""

    def __init__(self, use_semantic: bool = True):
        """
        Initialize the character classifier.

        Args:
            use_semantic: Whether to enable semantic similarity fallback
        """
        self.shay_keywords: Set[str] = set()
        self.lexie_keywords: Set[str] = set()
        self.shay_descriptors: str = ""
        self.lexie_descriptors: str = ""
        
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.semantic_model = None
        self.shay_embedding = None
        self.lexie_embedding = None
        self._semantic_model_loaded = False
        
        # Don't load model during init - load lazily only if needed
        # This avoids blocking on network requests when semantic similarity isn't available

    def _extract_keywords_from_markdown(self, md_path: Path) -> Dict[str, List[str]]:
        """
        Parse markdown file to extract descriptor keywords.

        Args:
            md_path: Path to markdown file

        Returns:
            Dictionary with extracted keywords and full descriptor text
        """
        keywords = {
            'tokens': [],
            'descriptor_text': ''
        }
        
        if not md_path.exists():
            return keywords
        
        try:
            content = md_path.read_text(encoding='utf-8')
            keywords['descriptor_text'] = content
            
            # Extract structured sections (FACE_STRUCTURE, SKIN, EYES, etc.)
            section_pattern = r'([A-Z_]+):\s*([^\n]+)'
            matches = re.findall(section_pattern, content)
            
            for section_name, section_value in matches:
                # Extract individual tokens/words
                tokens = re.findall(r'\b[a-z]+\b', section_value.lower())
                keywords['tokens'].extend(tokens)
            
            # Extract text from code blocks (character descriptions)
            code_block_pattern = r'```[^\n]*\n(.*?)```'
            code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
            for block in code_blocks:
                tokens = re.findall(r'\b[a-z]+\b', block.lower())
                keywords['tokens'].extend(tokens)
            
            # Extract character name if present
            name_pattern = r'\b(Shay|Lexie)\b'
            name_matches = re.findall(name_pattern, content, re.IGNORECASE)
            keywords['tokens'].extend([name.lower() for name in name_matches])
            
            # Remove duplicates while preserving order
            seen = set()
            keywords['tokens'] = [t for t in keywords['tokens'] if not (t in seen or seen.add(t))]
            
        except Exception as e:
            warnings.warn(f"Failed to parse markdown file {md_path}: {e}")
        
        return keywords

    def load_character_descriptors(
        self, 
        shay_path: Optional[Path] = None,
        lexie_path: Optional[Path] = None
    ) -> None:
        """
        Load character descriptors from markdown files.

        Args:
            shay_path: Path to Subject-Shay.md
            lexie_path: Path to Subject-Lexie.md (optional, may not exist yet)
        """
        # Default paths
        if shay_path is None:
            shay_path = Path("data/Prompts/Subject-Shay.md")
        if lexie_path is None:
            lexie_path = Path("data/Prompts/Subject-Lexie.md")
        
        # Load Shay descriptors
        shay_data = self._extract_keywords_from_markdown(Path(shay_path))
        self.shay_keywords = set(shay_data['tokens'])
        self.shay_descriptors = shay_data['descriptor_text']
        
        # Add explicit "shay" keyword
        self.shay_keywords.add('shay')
        
        # Load Lexie descriptors (if file exists)
        if Path(lexie_path).exists():
            lexie_data = self._extract_keywords_from_markdown(Path(lexie_path))
            self.lexie_keywords = set(lexie_data['tokens'])
            self.lexie_descriptors = lexie_data['descriptor_text']
        else:
            # If Lexie file doesn't exist, use minimal keywords
            self.lexie_keywords = {'lexie'}
            self.lexie_descriptors = ""
        
        # Add explicit "lexie" keyword
        self.lexie_keywords.add('lexie')
        
        # Update semantic embeddings if available (lazy load model)
        if self.use_semantic:
            self._ensure_semantic_model_loaded()
            if self.semantic_model:
                try:
                    if self.shay_descriptors:
                        self.shay_embedding = self.semantic_model.encode(
                            self.shay_descriptors[:512],  # Limit length
                            normalize_embeddings=True
                        )
                    if self.lexie_descriptors:
                        self.lexie_embedding = self.semantic_model.encode(
                            self.lexie_descriptors[:512],
                            normalize_embeddings=True
                        )
                except Exception as e:
                    warnings.warn(f"Failed to create semantic embeddings: {e}")
                    self.use_semantic = False

    def _rule_based_classify(self, prompt: str) -> Optional[str]:
        """
        Rule-based classification using keyword matching.

        Args:
            prompt: Prompt text to classify

        Returns:
            "shay", "lexie", or None if no match
        """
        prompt_lower = prompt.lower()
        
        # Check for explicit character names first
        if 'shay' in prompt_lower:
            return 'shay'
        if 'lexie' in prompt_lower:
            return 'lexie'
        
        # Strong Lexie indicators (check these first as they're distinctive)
        lexie_strong_indicators = [
            'hazel-green eyes',
            'hazel green eyes',
            'green eyes',
            'taller than 6ft',
            'taller than 6 ft',
        ]
        
        for indicator in lexie_strong_indicators:
            if indicator in prompt_lower:
                return 'lexie'
        
        # Check for "6ft" or "6 ft" with height context (Lexie indicator)
        if re.search(r'6\s*ft', prompt_lower) and ('taller' in prompt_lower or 'height' in prompt_lower or 'door frame' in prompt_lower):
            return 'lexie'
        
        # Count keyword matches
        shay_matches = sum(1 for kw in self.shay_keywords if kw in prompt_lower)
        lexie_matches = sum(1 for kw in self.lexie_keywords if kw in prompt_lower)
        
        # Require at least 2 keyword matches to classify (or 1 strong match)
        if shay_matches >= 2 and shay_matches > lexie_matches:
            return 'shay'
        elif lexie_matches >= 2 and lexie_matches > shay_matches:
            return 'lexie'
        elif lexie_matches >= 1 and 'hazel' in prompt_lower and 'green' in prompt_lower:
            # Single match but with hazel-green combo is strong indicator
            return 'lexie'
        
        return None

    def _ensure_semantic_model_loaded(self) -> None:
        """Lazily load the semantic model only when needed."""
        if self._semantic_model_loaded or not self.use_semantic:
            return
        
        if self.semantic_model is None:
            try:
                # Use a lightweight model for fast inference
                # Note: If network is unavailable, this will fail gracefully
                # and fall back to rule-based classification
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Model download timed out")
                
                # Set a timeout for model loading (10 seconds)
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(10)
                
                try:
                    self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                    signal.alarm(0)  # Cancel alarm
                    self._semantic_model_loaded = True
                except (TimeoutError, Exception) as e:
                    signal.alarm(0)  # Cancel alarm
                    # Silently disable semantic - rule-based will be used instead
                    warnings.warn(f"Semantic model unavailable (network issue?): {str(e)[:100]}. Using rule-based classification only.")
                    self.use_semantic = False
                    self._semantic_model_loaded = True  # Mark as loaded to prevent retries
            except (AttributeError, OSError):
                # signal module may not work in all environments (e.g., Windows, some Docker setups)
                # Just try to load without timeout
                try:
                    self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                    self._semantic_model_loaded = True
                except Exception as e:
                    warnings.warn(f"Semantic model unavailable: {str(e)[:100]}. Using rule-based classification only.")
                    self.use_semantic = False
                    self._semantic_model_loaded = True

    def _semantic_classify(self, prompt: str) -> Optional[str]:
        """
        Semantic similarity-based classification (fallback).

        Args:
            prompt: Prompt text to classify

        Returns:
            "shay", "lexie", or None if confidence is low
        """
        if not self.use_semantic:
            return None
        
        self._ensure_semantic_model_loaded()
        if not self.semantic_model:
            return None
        
        if not self.shay_embedding or not self.lexie_embedding:
            return None
        
        try:
            prompt_embedding = self.semantic_model.encode(
                prompt[:512],
                normalize_embeddings=True
            )
            
            # Calculate cosine similarity
            shay_sim = np.dot(prompt_embedding, self.shay_embedding)
            lexie_sim = np.dot(prompt_embedding, self.lexie_embedding)
            
            # Require similarity > 0.3 to classify
            threshold = 0.3
            if shay_sim > threshold and shay_sim > lexie_sim:
                return 'shay'
            elif lexie_sim > threshold and lexie_sim > shay_sim:
                return 'lexie'
            
        except Exception as e:
            warnings.warn(f"Semantic classification failed: {e}")
        
        return None

    def classify_character(self, prompt: str) -> str:
        """
        Classify a prompt into character cluster.

        Args:
            prompt: Prompt text to classify

        Returns:
            "shay", "lexie", or "universal"
        """
        if not prompt or not isinstance(prompt, str):
            return 'universal'
        
        # Primary: Rule-based classification
        classification = self._rule_based_classify(prompt)
        
        # Fallback: Semantic similarity (if rule-based didn't match)
        if classification is None and self.use_semantic:
            classification = self._semantic_classify(prompt)
        
        # Default to universal if no classification
        return classification if classification else 'universal'

