"""
Template script for batch generating Shay dataset images using nanobanana (Gemini 3 Image Pro).

This script reads the Subject-Shay-dataset.json file and generates prompts
ready for batch processing with nanobanana API or interface.
"""

import json
from pathlib import Path


def load_dataset_config():
    """Load the dataset configuration from JSON."""
    config_path = Path(__file__).parent / "Subject-Shay-dataset.json"
    with open(config_path, "r") as f:
        return json.load(f)


def generate_full_prompt(base_identity, prompt_text):
    """Combine base identity with specific prompt variation."""
    return f"{base_identity}\n\n{prompt_text}"


def generate_batch_prompts(group_filter=None, output_format="full"):
    """
    Generate batch prompts for nanobanana.
    
    Args:
        group_filter: Optional filter by group (e.g., "neutral_reference", "expression_diversity")
        output_format: "full" for complete prompts, "variations" for just the variation text
    
    Returns:
        List of prompt dictionaries with metadata
    """
    config = load_dataset_config()
    base_identity = config["character"]["base_identity"]
    
    prompts = []
    for prompt_data in config["prompts"]:
        if group_filter and prompt_data["group"] != group_filter:
            continue
        
        if output_format == "full":
            full_prompt = generate_full_prompt(base_identity, prompt_data["full_prompt"])
        else:
            full_prompt = prompt_data["full_prompt"]
        
        prompts.append({
            "id": prompt_data["id"],
            "name": prompt_data["name"],
            "group": prompt_data["group"],
            "prompt": full_prompt,
            "metadata": prompt_data["metadata"],
            "captions": prompt_data["captions"]
        })
    
    return prompts


def export_for_nanobanana(output_file="shay_batch_prompts.txt", group_filter=None):
    """
    Export prompts in a format ready for nanobanana batch processing.
    
    Each prompt is separated by a clear delimiter for easy parsing.
    """
    prompts = generate_batch_prompts(group_filter=group_filter, output_format="full")
    
    output_path = Path(__file__).parent / output_file
    
    with open(output_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("SHAY DATASET GENERATION PROMPTS FOR NANOBANANA\n")
        f.write("=" * 80 + "\n\n")
        
        for i, prompt_data in enumerate(prompts, 1):
            f.write(f"\n{'=' * 80}\n")
            f.write(f"PROMPT {i}/{len(prompts)}: {prompt_data['id']} - {prompt_data['name']}\n")
            f.write(f"Group: {prompt_data['group']}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(prompt_data["prompt"])
            f.write("\n\n")
            f.write("-" * 80 + "\n")
            f.write("METADATA:\n")
            f.write(f"  Hairstyle: {prompt_data['metadata']['hairstyle']}\n")
            f.write(f"  Expression: {prompt_data['metadata']['expression']}\n")
            f.write(f"  Angle: {prompt_data['metadata']['angle']}\n")
            f.write(f"  Lighting: {prompt_data['metadata']['lighting']}\n")
            f.write(f"  Clothing: {prompt_data['metadata']['clothing']}\n")
            f.write(f"  Framing: {prompt_data['metadata']['framing']}\n")
            f.write("-" * 80 + "\n\n")
    
    print(f"Exported {len(prompts)} prompts to {output_path}")
    return output_path


def export_captions_for_training(model="z_image_turbo", output_file=None):
    """
    Export training captions for a specific model.
    
    Args:
        model: "z_image_turbo", "flux", or "qwen_image"
        output_file: Optional custom output filename
    """
    config = load_dataset_config()
    
    if output_file is None:
        output_file = f"shay_captions_{model}.txt"
    
    output_path = Path(__file__).parent / output_file
    
    with open(output_path, "w") as f:
        for prompt_data in config["prompts"]:
            caption = prompt_data["captions"][model]
            f.write(f"{caption}\n")
    
    print(f"Exported {len(config['prompts'])} captions for {model} to {output_path}")
    return output_path


def generate_wildcard_combinations():
    """
    Generate example wildcard combinations for automated prompt generation.
    Useful for creating variations beyond the base 32-image set.
    """
    config = load_dataset_config()
    wildcards = config["wildcards"]
    
    examples = []
    # Example: Generate a few random combinations
    import random
    
    for _ in range(5):
        combo = {
            "hairstyle": random.choice(wildcards["hairstyles"]),
            "expression": random.choice(wildcards["expressions"]),
            "angle": random.choice(wildcards["angles"]),
            "lighting": random.choice(wildcards["lighting"]),
            "clothing": random.choice(wildcards["clothing"]),
            "background": random.choice(wildcards["backgrounds"]),
            "framing": random.choice(wildcards["framing"])
        }
        examples.append(combo)
    
    return examples


if __name__ == "__main__":
    # Example usage:
    
    # Export all prompts for nanobanana
    export_for_nanobanana()
    
    # Export captions for each model
    for model in ["z_image_turbo", "flux", "qwen_image"]:
        export_captions_for_training(model=model)
    
    # Export specific group only
    # export_for_nanobanana("neutral_reference_only.txt", group_filter="neutral_reference")
    
    print("\nBatch generation templates ready!")
    print("Use the exported .txt files with nanobanana for batch image generation.")









