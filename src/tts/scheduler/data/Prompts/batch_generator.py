"""
Batch generator for Shay character prompts using wildcard system.

Parses Markdown wildcard files and generates prompt combinations for nanobanana-3.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from itertools import product
import random


def parse_markdown_wildcard(file_path: Path) -> Dict[str, Dict[str, str]]:
    """
    Parse a Markdown wildcard file and extract structured data.
    
    Expected format:
    ## id
    - **Short**: "short description"
    - **Description**: full description
    - **Camera Notes**: optional notes
    
    Returns:
        Dictionary mapping wildcard IDs to their data
    """
    wildcards = {}
    
    if not file_path.exists():
        return wildcards
    
    content = file_path.read_text(encoding='utf-8')
    
    # Split by ## headers (wildcard IDs)
    sections = re.split(r'^##\s+(\w+)\s*$', content, flags=re.MULTILINE)
    
    # Skip first element (content before first header)
    for i in range(1, len(sections), 2):
        if i + 1 >= len(sections):
            break
        
        wildcard_id = sections[i].strip()
        section_content = sections[i + 1].strip()
        
        # Extract fields
        short_match = re.search(r'\*\*Short\*\*:\s*"([^"]+)"', section_content)
        desc_match = re.search(r'\*\*Description\*\*:\s*(.+?)(?=\n-|\Z)', section_content, re.DOTALL)
        camera_match = re.search(r'\*\*Camera Notes\*\*:\s*(.+?)(?=\n-|\Z)', section_content, re.DOTALL)
        
        wildcards[wildcard_id] = {
            'id': wildcard_id,
            'short': short_match.group(1) if short_match else '',
            'description': desc_match.group(1).strip() if desc_match else '',
            'camera_notes': camera_match.group(1).strip() if camera_match else ''
        }
    
    return wildcards


def load_identity_template() -> str:
    """Load the base identity template from identity.md"""
    identity_path = Path(__file__).parent / "identity.md"
    
    if not identity_path.exists():
        return ""
    
    content = identity_path.read_text(encoding='utf-8')
    
    # Extract the base identity template section
    match = re.search(
        r'## Base Identity Template for nanobanana-3.*?\n\n```\n(.*?)\n```',
        content,
        re.DOTALL
    )
    
    if match:
        return match.group(1).strip()
    
    # Fallback: look for any code block with identity content
    match = re.search(r'```\n(.*?A realistic photograph of Shay.*?)\n```', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return ""


def load_all_wildcards() -> Dict[str, Dict[str, Dict[str, str]]]:
    """Load all wildcard files from the wildcards directory."""
    wildcards_dir = Path(__file__).parent / "wildcards"
    
    categories = {
        'hairstyles': 'hairstyles.md',
        'outfits': 'outfits.md',
        'poses': 'poses.md',
        'framing': 'framing.md',
        'lighting': 'lighting.md',
        'backgrounds': 'backgrounds.md'
    }
    
    all_wildcards = {}
    
    for category, filename in categories.items():
        file_path = wildcards_dir / filename
        all_wildcards[category] = parse_markdown_wildcard(file_path)
    
    return all_wildcards


def generate_prompt(
    identity: str,
    hairstyle: Dict[str, str],
    outfit: Dict[str, str],
    pose: Dict[str, str],
    framing: Dict[str, str],
    lighting: Dict[str, str],
    background: Dict[str, str]
) -> str:
    """
    Generate a complete prompt by combining identity with wildcard selections.
    """
    # Build the prompt variation
    variation_parts = []
    
    # Add framing/angle description
    if pose['description']:
        variation_parts.append(pose['description'])
    
    # Add expression if not already in pose
    if 'expression' in pose['short'].lower():
        pass  # Already included
    else:
        # Extract expression from pose if available
        pass
    
    # Add hairstyle
    if hairstyle['description']:
        variation_parts.append(f"Hair: {hairstyle['description']}")
    
    # Add outfit
    if outfit['description']:
        variation_parts.append(f"Wearing: {outfit['description']}")
    
    # Add lighting
    if lighting['description']:
        variation_parts.append(f"Lighting: {lighting['description']}")
    
    # Add background
    if background['description']:
        variation_parts.append(f"Background: {background['description']}")
    
    # Add framing
    if framing['description']:
        variation_parts.append(f"Framing: {framing['description']}")
    
    variation = ". ".join(variation_parts) + "."
    
    # Combine with identity
    full_prompt = f"{identity}\n\n{variation}"
    
    return full_prompt


def generate_combinations(
    mode: str = "curated",
    max_combinations: int = 32,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate prompt combinations based on mode.
    
    Args:
        mode: "full" (cartesian product), "curated" (subset), or "random" (sampling)
        max_combinations: Maximum number of combinations for curated/random modes
        seed: Random seed for reproducible random sampling
    
    Returns:
        List of prompt dictionaries with metadata
    """
    identity = load_identity_template()
    all_wildcards = load_all_wildcards()
    
    if seed is not None:
        random.seed(seed)
    
    # Get all wildcard options
    hairstyles = list(all_wildcards['hairstyles'].values())
    outfits = list(all_wildcards['outfits'].values())
    poses = list(all_wildcards['poses'].values())
    framings = list(all_wildcards['framing'].values())
    lightings = list(all_wildcards['lighting'].values())
    backgrounds = list(all_wildcards['backgrounds'].values())
    
    if mode == "full":
        # Full cartesian product
        combinations = list(product(hairstyles, outfits, poses, framings, lightings, backgrounds))
    elif mode == "curated":
        # Curated subset - prioritize diversity
        # Select diverse combinations manually
        combinations = _generate_curated_combinations(
            hairstyles, outfits, poses, framings, lightings, backgrounds, max_combinations
        )
    else:  # random
        # Random sampling
        combinations = []
        for _ in range(max_combinations):
            combo = (
                random.choice(hairstyles),
                random.choice(outfits),
                random.choice(poses),
                random.choice(framings),
                random.choice(lightings),
                random.choice(backgrounds)
            )
            combinations.append(combo)
    
    # Generate prompts
    prompts = []
    for i, (hairstyle, outfit, pose, framing, lighting, background) in enumerate(combinations[:max_combinations], 1):
        prompt_text = generate_prompt(identity, hairstyle, outfit, pose, framing, lighting, background)
        
        prompts.append({
            'id': f"P{i:03d}",
            'prompt': prompt_text,
            'metadata': {
                'hairstyle': hairstyle['id'],
                'outfit': outfit['id'],
                'pose': pose['id'],
                'framing': framing['id'],
                'lighting': lighting['id'],
                'background': background['id'],
                'model': 'nanobanana-3'
            },
            'short_tags': {
                'hairstyle': hairstyle['short'],
                'outfit': outfit['short'],
                'pose': pose['short'],
                'framing': framing['short'],
                'lighting': lighting['short'],
                'background': background['short']
            }
        })
    
    return prompts


def _generate_curated_combinations(
    hairstyles: List[Dict],
    outfits: List[Dict],
    poses: List[Dict],
    framings: List[Dict],
    lightings: List[Dict],
    backgrounds: List[Dict],
    max_count: int
) -> List[tuple]:
    """
    Generate a curated subset that ensures diversity across all categories.
    """
    combinations = []
    
    # Prioritize key variations for dataset diversity
    key_hairstyles = ['down', 'ponytail', 'claw_clip_half_up']
    key_poses = ['neutral_frontal', 'genuine_smile_frontal', 'slight_3_4_right', 'slight_3_4_left']
    key_framings = ['head_shoulders', 'medium_shot']
    key_lightings = ['soft_window_indoor', 'studio_professional', 'golden_hour_outdoor']
    
    # Build diverse combinations
    for hairstyle in hairstyles:
        if len(combinations) >= max_count:
            break
        for pose in poses:
            if len(combinations) >= max_count:
                break
            for framing in framings:
                if len(combinations) >= max_count:
                    break
                for lighting in lightings:
                    if len(combinations) >= max_count:
                        break
                    # Add variety in outfits and backgrounds
                    for outfit in outfits[:5]:  # Limit outfit variety
                        if len(combinations) >= max_count:
                            break
                        for background in backgrounds[:3]:  # Limit background variety
                            if len(combinations) >= max_count:
                                break
                            combinations.append((hairstyle, outfit, pose, framing, lighting, background))
    
    # If we need more, add random ones
    if len(combinations) < max_count:
        needed = max_count - len(combinations)
        for _ in range(needed):
            combo = (
                random.choice(hairstyles),
                random.choice(outfits),
                random.choice(poses),
                random.choice(framings),
                random.choice(lightings),
                random.choice(backgrounds)
            )
            if combo not in combinations:
                combinations.append(combo)
    
    return combinations[:max_count]


def export_prompts(
    prompts: List[Dict[str, Any]],
    output_file: str = "shay_batch_prompts.txt"
) -> Path:
    """
    Export prompts to a text file for nanobanana batch processing.
    """
    output_path = Path(__file__).parent / output_file
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SHAY DATASET GENERATION PROMPTS FOR NANOBANANA-3\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Prompts: {len(prompts)}\n")
        f.write(f"Model: nanobanana-3 (Gemini 3 Image Pro)\n")
        f.write("=" * 80 + "\n\n")
        
        for i, prompt_data in enumerate(prompts, 1):
            f.write(f"\n{'=' * 80}\n")
            f.write(f"PROMPT {i}/{len(prompts)}: {prompt_data['id']}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(prompt_data['prompt'])
            f.write("\n\n")
            f.write("-" * 80 + "\n")
            f.write("METADATA:\n")
            for key, value in prompt_data['metadata'].items():
                f.write(f"  {key}: {value}\n")
            f.write("\nSHORT TAGS:\n")
            for key, value in prompt_data['short_tags'].items():
                f.write(f"  {key}: {value}\n")
            f.write("-" * 80 + "\n\n")
    
    print(f"Exported {len(prompts)} prompts to {output_path}")
    return output_path


def export_json(
    prompts: List[Dict[str, Any]],
    output_file: str = "shay_batch_prompts.json"
) -> Path:
    """
    Export prompts to JSON format.
    """
    import json
    
    output_path = Path(__file__).parent / output_file
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'model': 'nanobanana-3',
            'total_prompts': len(prompts),
            'prompts': prompts
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(prompts)} prompts to {output_path}")
    return output_path


if __name__ == "__main__":
    # Example usage
    
    print("Loading wildcards and generating prompts...")
    
    # Generate curated 32-image dataset
    prompts = generate_combinations(mode="curated", max_combinations=32)
    
    # Export to text file
    export_prompts(prompts, "shay_batch_prompts_nanobanana3.txt")
    
    # Export to JSON
    export_json(prompts, "shay_batch_prompts_nanobanana3.json")
    
    print(f"\nGenerated {len(prompts)} prompts for nanobanana-3")
    print("Use the exported files with nanobanana for batch image generation.")










