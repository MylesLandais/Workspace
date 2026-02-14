"""
Prompt Builder - Construct Prompt objects from wildcard selections

Builders compose wildcard values into Prompt objects.
Templates are pluggable - define your own and pass them in.
String formatting handled by Prompt.__str__ for easy serialization.

Usage:
    from prompt_builder import PromptBuilder, Prompt

    builder = PromptBuilder(wildcards_dir="wildcards_yaml")

    # Define template (Jinja2 syntax)
    template = "{{ character.shay.base_identity }} ... {{ pose.description }}"

    prompt = builder.compose(
        template=template,
        selections={
            "pose_id": "vajrasana",
            "variation_id": "base",
            "hairstyle": "high_ponytail"
        }
    )

    print(prompt)  # Calls __str__ for formatted output
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from jinja2 import Environment, BaseLoader


@dataclass
class Prompt:
    """A constructed prompt object."""

    id: str
    prompt_type: str
    full_prompt: str
    metadata: Dict[str, Any]
    captions: Dict[str, str]

    def __str__(self) -> str:
        """String representation for serialization."""
        lines = [
            f"\n{'=' * 80}",
            f"PROMPT: {self.id}",
            f"{'=' * 80}\n",
            self.full_prompt,
            f"\n{'-' * 80}",
            "METADATA:"
        ]

        for key, value in self.metadata.items():
            lines.append(f"  {key}: {value}")

        lines.append("\nCAPTIONS:")
        for model, caption in self.captions.items():
            lines.append(f"  {model}: {caption}")

        lines.append(f"{'-' * 80}\n")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Prompt(id={self.id!r}, type={self.prompt_type!r})"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WildcardLoader:
    """Load and cache YAML wildcard files."""

    def __init__(self, wildcards_dir: Path):
        self.wildcards_dir = Path(wildcards_dir)
        self._cache: Dict[str, Any] = {}

    def load(self, filename: str) -> Dict[str, Any]:
        """Load a YAML wildcard file."""
        if filename in self._cache:
            return self._cache[filename]

        filepath = self.wildcards_dir / f"{filename}.yaml"
        if not filepath.exists():
            raise FileNotFoundError(f"Wildcard not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        self._cache[filename] = data or {}
        return self._cache[filename]


class PromptBuilder:
    """Builder for constructing Prompt objects."""

    def __init__(self, wildcards_dir: str = "wildcards_yaml"):
        self.wildcards_dir = Path(wildcards_dir)
        self.loader = WildcardLoader(self.wildcards_dir)
        self.jinja = Environment(loader=BaseLoader())
        self._counter = 0

    def _next_id(self, prefix: str = "PROMPT") -> str:
        self._counter += 1
        return f"{prefix}{self._counter:03d}"

    def _load_wildcards_for_context(self, wildcard_files: List[str]) -> Dict[str, Any]:
        """Load multiple wildcard files for template context."""
        context = {}
        for filename in wildcard_files:
            context[filename] = self.loader.load(filename)
        return context

    def compose(
        self,
        template: str,
        selections: Dict[str, Any],
        prompt_type: str = "custom",
        wildcard_files: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        captions: Optional[Dict[str, str]] = None,
        prompt_id: Optional[str] = None
    ) -> Prompt:
        """
        Compose a Prompt using a Jinja2 template and wildcard selections.

        Args:
            template: Jinja2 template string with {{ variable }} syntax
            selections: Dict of variable selections to pass to template
            prompt_type: Type identifier (e.g., "yoga_pose", "portrait")
            wildcard_files: List of wildcard files to load as context
            metadata: Optional metadata dict
            captions: Optional captions dict (model-specific)
            prompt_id: Optional custom prompt ID

        Returns:
            Prompt object
        """

        # Load wildcards if files specified
        context = {}
        if wildcard_files:
            context.update(self._load_wildcards_for_context(wildcard_files))

        # Add selections to context
        context.update(selections)

        # Render template
        tmpl = self.jinja.from_string(template)
        full_prompt = tmpl.render(context)

        pid = prompt_id or self._next_id("PROMPT")

        return Prompt(
            id=pid,
            prompt_type=prompt_type,
            full_prompt=full_prompt,
            metadata=metadata or {},
            captions=captions or {}
        )

    def compose_batch(
        self,
        template: str,
        variation_params: List[Dict[str, Any]],
        prompt_type: str = "custom",
        wildcard_files: Optional[List[str]] = None,
        base_metadata: Optional[Dict[str, Any]] = None,
        base_captions: Optional[Dict[str, str]] = None
    ) -> List[Prompt]:
        """
        Compose multiple prompts from variations of the same template.

        Args:
            template: Base template string
            variation_params: List of dicts, each defining a variation
            prompt_type: Type identifier
            wildcard_files: Wildcard files to load
            base_metadata: Metadata added to all prompts
            base_captions: Captions added to all prompts

        Returns:
            List of Prompt objects
        """

        prompts = []

        for i, variations in enumerate(variation_params, 1):
            metadata = {**(base_metadata or {}), **variations.get("metadata", {})}
            captions = {**(base_captions or {}), **variations.get("captions", {})}
            selections = {k: v for k, v in variations.items() if k not in ["metadata", "captions"]}

            prompt = self.compose(
                template=template,
                selections=selections,
                prompt_type=prompt_type,
                wildcard_files=wildcard_files,
                metadata=metadata,
                captions=captions,
                prompt_id=variations.get("prompt_id") or self._next_id(prompt_type[:3].upper())
            )

            prompts.append(prompt)

        return prompts


if __name__ == "__main__":
    print("PromptBuilder module ready")
    print("Usage: builder = PromptBuilder()")
    print("       prompt = builder.compose(template='...', selections={...})")
