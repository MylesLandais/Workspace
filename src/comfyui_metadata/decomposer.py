"""
Prompt Decomposer for ComfyUI Prompts

Decomposes prompts into structured components: core subject, action/pose,
template, style modifiers, and technical tokens.
"""

import re
from typing import Dict, List, Set, Optional


class PromptDecomposer:
    """Decomposes prompts into structured components."""

    def __init__(self):
        """Initialize the prompt decomposer with keyword dictionaries."""
        # Action/Pose keywords
        self.action_keywords: Set[str] = {
            'sitting', 'standing', 'fighting', 'walking', 'running', 'jumping',
            'laying', 'lying', 'kneeling', 'crouching', 'leaning', 'bending',
            'dancing', 'posing', 'striking', 'punching', 'kicking', 'grabbing',
            'holding', 'pointing', 'waving', 'smiling', 'laughing', 'crying',
            'looking', 'staring', 'gazing', 'winking', 'blowing', 'kissing',
            'hugging', 'embracing', 'reaching', 'stretching', 'twisting',
            'turning', 'facing', 'back', 'front', 'side', 'profile'
        }
        
        # Common pose descriptors
        self.pose_descriptors: Set[str] = {
            'pose', 'position', 'stance', 'posture', 'gesture', 'expression',
            'action', 'movement', 'motion', 'dynamic', 'static'
        }
        
        # Background/environment keywords (template)
        self.template_keywords: Set[str] = {
            'background', 'environment', 'scene', 'setting', 'location',
            'city', 'forest', 'beach', 'mountain', 'desert', 'ocean',
            'indoor', 'outdoor', 'room', 'house', 'building', 'street',
            'park', 'garden', 'studio', 'warehouse', 'cafe', 'restaurant',
            'sunset', 'sunrise', 'day', 'night', 'evening', 'morning',
            'weather', 'rain', 'snow', 'clouds', 'sunny', 'foggy'
        }
        
        # Style keywords (art styles, genres)
        self.style_keywords: Set[str] = {
            'realistic', 'photorealistic', 'photography', 'photograph',
            'anime', 'manga', 'cartoon', 'comic', 'illustration', 'drawing',
            'painting', 'watercolor', 'oil', 'digital', 'sketch', 'concept',
            'cyberpunk', 'steampunk', 'fantasy', 'sci-fi', 'horror', 'noir',
            'vintage', 'retro', 'modern', 'contemporary', 'classical',
            'abstract', 'impressionist', 'surreal', 'minimalist'
        }
        
        # Technical/quality tokens
        self.technical_tokens: Set[str] = {
            'masterpiece', 'best quality', 'high quality', 'ultra quality',
            'highly detailed', 'ultra detailed', 'extremely detailed',
            '8k', '4k', '2k', 'hd', 'uhd', 'high resolution',
            'sharp', 'crisp', 'clear', 'clean', 'perfect', 'flawless',
            'professional', 'award winning', 'trending', 'popular'
        }
        
        # Common artist/style modifier patterns (to be expanded)
        self.artist_patterns: List[re.Pattern] = [
            re.compile(r'\bby\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.IGNORECASE),
            re.compile(r'\bin\s+the\s+style\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.IGNORECASE),
        ]

    def _extract_tokens(self, prompt: str, keywords: Set[str]) -> List[str]:
        """
        Extract matching tokens from prompt.

        Args:
            prompt: Prompt text
            keywords: Set of keywords to match

        Returns:
            List of matched tokens
        """
        prompt_lower = prompt.lower()
        matched = []
        
        for keyword in keywords:
            # Match whole words
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, prompt_lower):
                matched.append(keyword)
        
        return matched

    def _extract_phrases(self, prompt: str, keywords: Set[str]) -> List[str]:
        """
        Extract phrases containing keywords.

        Args:
            prompt: Prompt text
            keywords: Set of keywords to match

        Returns:
            List of matched phrases (3-5 words around keyword)
        """
        prompt_lower = prompt.lower()
        matched_phrases = []
        words = prompt_lower.split()
        
        for i, word in enumerate(words):
            # Check if word contains any keyword
            for keyword in keywords:
                if keyword in word or word in keyword:
                    # Extract context (2 words before, 2 after)
                    start = max(0, i - 2)
                    end = min(len(words), i + 3)
                    phrase = ' '.join(words[start:end])
                    matched_phrases.append(phrase)
                    break
        
        return matched_phrases

    def decompose_prompt(self, prompt: str, character_cluster: Optional[str] = None) -> Dict[str, str]:
        """
        Decompose a prompt into structured components.

        Args:
            prompt: Prompt text to decompose
            character_cluster: Character classification ("shay", "lexie", "universal")

        Returns:
            Dictionary with keys: core_subject, action_pose, template,
            style_modifiers, technical_tokens
        """
        if not prompt:
            return {
                'core_subject': '',
                'action_pose': '',
                'template': '',
                'style_modifiers': '',
                'technical_tokens': ''
            }
        
        result = {
            'core_subject': '',
            'action_pose': '',
            'template': '',
            'style_modifiers': '',
            'technical_tokens': ''
        }
        
        # Extract core subject
        if character_cluster and character_cluster != 'universal':
            result['core_subject'] = character_cluster.capitalize()
        else:
            # Check for explicit character mentions
            if 'shay' in prompt.lower():
                result['core_subject'] = 'Shay'
            elif 'lexie' in prompt.lower():
                result['core_subject'] = 'Lexie'
            else:
                result['core_subject'] = 'Unknown'
        
        # Extract action/pose
        action_tokens = self._extract_tokens(prompt, self.action_keywords)
        pose_tokens = self._extract_tokens(prompt, self.pose_descriptors)
        all_action_pose = list(set(action_tokens + pose_tokens))
        result['action_pose'] = ', '.join(all_action_pose) if all_action_pose else ''
        
        # Extract template (environment/background)
        template_tokens = self._extract_tokens(prompt, self.template_keywords)
        template_phrases = self._extract_phrases(prompt, self.template_keywords)
        # Combine tokens and unique phrases
        all_template = list(set(template_tokens + template_phrases[:5]))  # Limit phrases
        result['template'] = ', '.join(all_template) if all_template else ''
        
        # Extract style modifiers
        style_tokens = self._extract_tokens(prompt, self.style_keywords)
        
        # Extract artist names using patterns
        artist_matches = []
        for pattern in self.artist_patterns:
            matches = pattern.findall(prompt)
            artist_matches.extend(matches)
        
        all_style = list(set(style_tokens + artist_matches))
        result['style_modifiers'] = ', '.join(all_style) if all_style else ''
        
        # Extract technical tokens
        technical_tokens = self._extract_tokens(prompt, self.technical_tokens)
        result['technical_tokens'] = ', '.join(technical_tokens) if technical_tokens else ''
        
        return result


