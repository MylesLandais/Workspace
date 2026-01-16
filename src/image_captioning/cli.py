"""
Command-line interface for image captioning system.
"""

import argparse
from pathlib import Path
from typing import Optional

from .tag_manager import TagManager
from .io import CaptionIO
from .config import CaptionConfig


def tag_images(args):
    """Auto-tag images in a directory."""
    directory = Path(args.directory)
    config = CaptionConfig()
    if args.config:
        # Load config from file if provided
        pass  # TODO: Implement config loading
    
    manager = TagManager(config)
    print(f"Auto-tagging images in {directory}...")
    captions = manager.auto_tag_directory(directory)
    print(f"Tagged {len(captions)} images")
    
    # Save results
    if args.output:
        output_path = Path(args.output)
        CaptionIO.save_jsonl(captions, output_path)
        print(f"Saved captions to {output_path}")
    else:
        # Save to metadata.jsonl in the directory
        CaptionIO.save_to_directory(captions, directory)
        print(f"Saved captions to {directory / 'metadata.jsonl'}")


def add_manual_tags(args):
    """Add manual tags to specific images."""
    manager = TagManager()
    
    # Load existing captions if available
    directory = Path(args.directory)
    metadata_path = directory / "metadata.jsonl"
    if metadata_path.exists():
        captions = CaptionIO.load_jsonl(metadata_path)
        manager.captions = captions
    
    # Add tags
    for tag in args.tags:
        manager.add_manual_tag(args.filename, tag, confidence=1.0)
    
    # Save updated captions
    CaptionIO.save_to_directory(manager.captions, directory)
    print(f"Added manual tags to {args.filename}")


def set_bias(args):
    """Set user bias weights for classes/personas."""
    manager = TagManager()
    
    # Load existing captions if available
    directory = Path(args.directory)
    metadata_path = directory / "metadata.jsonl"
    if metadata_path.exists():
        captions = CaptionIO.load_jsonl(metadata_path)
        manager.captions = captions
    
    # Set bias
    manager.set_bias(args.persona_or_class, args.weight)
    
    # Save updated captions
    CaptionIO.save_to_directory(manager.captions, directory)
    print(f"Set bias for {args.persona_or_class} to {args.weight}")


def export_jsonl(args):
    """Export captions to JSONL format."""
    directory = Path(args.directory)
    metadata_path = directory / "metadata.jsonl"
    
    if not metadata_path.exists():
        print(f"Error: {metadata_path} does not exist")
        return
    
    captions = CaptionIO.load_jsonl(metadata_path)
    output_path = Path(args.output)
    CaptionIO.save_jsonl(captions, output_path)
    print(f"Exported {len(captions)} captions to {output_path}")


def export_txt(args):
    """Export captions to .txt files."""
    directory = Path(args.directory)
    metadata_path = directory / "metadata.jsonl"
    
    if not metadata_path.exists():
        print(f"Error: {metadata_path} does not exist")
        return
    
    captions = CaptionIO.load_jsonl(metadata_path)
    CaptionIO.export_txt(captions, directory)
    print(f"Exported {len(captions)} .txt caption files to {directory}")


def sort_by_class(args):
    """Sort/organize images by persona/class."""
    directory = Path(args.directory)
    metadata_path = directory / "metadata.jsonl"
    
    if not metadata_path.exists():
        print(f"Error: {metadata_path} does not exist")
        return
    
    manager = TagManager()
    captions = CaptionIO.load_jsonl(metadata_path)
    manager.captions = captions
    
    # Sort by class
    sorted_captions = manager.sort_by_weight(args.persona_or_class)
    
    # Print results
    print(f"\nSorted by {args.persona_or_class or 'total weight'}:")
    for i, caption in enumerate(sorted_captions[:args.limit], 1):
        weights = manager.calculate_final_weights(caption)
        total_weight = sum(weights.values())
        print(f"{i}. {caption.file_name} (weight: {total_weight:.2f})")
        if caption.personas:
            print(f"   Personas: {', '.join(caption.personas)}")
        if weights:
            top_tags = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"   Top tags: {', '.join([f'{tag}({w:.2f})' for tag, w in top_tags])}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Structured Image Captioning System")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")
    
    # tag-images command
    tag_parser = subparsers.add_parser("tag-images", help="Auto-tag images in a directory")
    tag_parser.add_argument("directory", type=str, help="Directory containing images")
    tag_parser.add_argument("--output", "-o", type=str, help="Output JSONL file path")
    tag_parser.add_argument("--config", "-c", type=str, help="Config file path")
    tag_parser.set_defaults(func=tag_images)
    
    # add-manual-tags command
    manual_parser = subparsers.add_parser("add-manual-tags", help="Add manual tags to specific images")
    manual_parser.add_argument("directory", type=str, help="Directory containing images")
    manual_parser.add_argument("filename", type=str, help="Image filename")
    manual_parser.add_argument("tags", nargs="+", help="Tags to add")
    manual_parser.set_defaults(func=add_manual_tags)
    
    # set-bias command
    bias_parser = subparsers.add_parser("set-bias", help="Set user bias weights for classes/personas")
    bias_parser.add_argument("directory", type=str, help="Directory containing images")
    bias_parser.add_argument("persona_or_class", type=str, help="Persona or class name")
    bias_parser.add_argument("weight", type=float, help="Bias weight")
    bias_parser.set_defaults(func=set_bias)
    
    # export-jsonl command
    jsonl_parser = subparsers.add_parser("export-jsonl", help="Export captions to JSONL format")
    jsonl_parser.add_argument("directory", type=str, help="Directory containing images")
    jsonl_parser.add_argument("output", type=str, help="Output JSONL file path")
    jsonl_parser.set_defaults(func=export_jsonl)
    
    # export-txt command
    txt_parser = subparsers.add_parser("export-txt", help="Export captions to .txt files")
    txt_parser.add_argument("directory", type=str, help="Directory containing images")
    txt_parser.set_defaults(func=export_txt)
    
    # sort-by-class command
    sort_parser = subparsers.add_parser("sort-by-class", help="Sort/organize images by persona/class")
    sort_parser.add_argument("directory", type=str, help="Directory containing images")
    sort_parser.add_argument("--persona-or-class", type=str, help="Persona or class to sort by")
    sort_parser.add_argument("--limit", type=int, default=20, help="Limit number of results")
    sort_parser.set_defaults(func=sort_by_class)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()








