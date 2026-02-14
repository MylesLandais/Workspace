#!/usr/bin/env python3
"""
ComfyUI Metadata Analyzer CLI

Command-line interface for analyzing ComfyUI image metadata,
classifying characters, decomposing prompts, and generating prompt books.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from comfyui_metadata import (
    BatchProcessor,
    CharacterClassifier,
    PromptDecomposer,
    TemplateAnalyzer,
    PromptBookGenerator,
    MetadataAnalyzer
)


def setup_paths() -> Tuple[Path, Path]:
    """Setup default paths for markdown files."""
    base_dir = Path(__file__).parent
    shay_path = base_dir / "data" / "Prompts" / "Subject-Shay.md"
    lexie_path = base_dir / "data" / "Prompts" / "Subject-Lexie.md"
    return shay_path, lexie_path


def cmd_extract(args):
    """Extract metadata from PNG files."""
    processor = BatchProcessor(
        classify_characters=False,
        decompose_prompts=False
    )
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        print(f"Current working directory: {Path.cwd()}")
        sys.exit(1)
    
    print(f"Extracting metadata from: {input_path}")
    try:
        df = processor.process_directory(
            input_path,
            recursive=args.recursive
        )
        print(f"Extracted {len(df)} records")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved to: {output_path}")


def cmd_classify(args):
    """Classify prompts by character."""
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Load CSV
    df = pd.read_csv(input_path)
    
    if 'positive_prompt' not in df.columns:
        print("Error: CSV must contain 'positive_prompt' column")
        sys.exit(1)
    
    # Setup classifier
    shay_path, lexie_path = setup_paths()
    classifier = CharacterClassifier()
    classifier.load_character_descriptors(shay_path, lexie_path)
    
    print("Classifying prompts...")
    df['character_cluster'] = df['positive_prompt'].apply(
        classifier.classify_character
    )
    
    # Print distribution
    print("\nClassification distribution:")
    print(df['character_cluster'].value_counts())
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")


def cmd_decompose(args):
    """Decompose prompts into components."""
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Load CSV
    df = pd.read_csv(input_path)
    
    if 'positive_prompt' not in df.columns:
        print("Error: CSV must contain 'positive_prompt' column")
        sys.exit(1)
    
    # Setup decomposer
    decomposer = PromptDecomposer()
    
    # Get character cluster if available
    has_cluster = 'character_cluster' in df.columns
    
    print("Decomposing prompts...")
    decomposition_results = []
    for idx, row in df.iterrows():
        prompt = row.get('positive_prompt', '')
        cluster = row.get('character_cluster', 'universal') if has_cluster else 'universal'
        decomposed = decomposer.decompose_prompt(prompt, cluster)
        decomposition_results.append(decomposed)
    
    # Add decomposition columns
    for key in ['core_subject', 'action_pose', 'template', 'style_modifiers', 'technical_tokens']:
        df[key] = [r[key] for r in decomposition_results]
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved to: {output_path}")


def cmd_analyze_templates(args):
    """Run template consistency and token impact analysis."""
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.parent / "template_analysis"
    
    # Load CSV
    df = pd.read_csv(input_path)
    
    required_cols = ['positive_prompt', 'character_cluster']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"Error: CSV must contain columns: {missing}")
        sys.exit(1)
    
    analyzer = TemplateAnalyzer()
    
    # Separate by cluster
    shay_df = df[df['character_cluster'] == 'shay']
    lexie_df = df[df['character_cluster'] == 'lexie']
    universal_df = df[df['character_cluster'] == 'universal']
    
    results = {}
    
    # Find common base
    if not shay_df.empty and not lexie_df.empty:
        print("Finding common base template...")
        common_base = analyzer.find_common_base(shay_df, lexie_df)
        results['common_base'] = common_base
        print(f"Common base: {common_base[:100]}...")
    
    # Token impact analysis
    print("Analyzing token impact...")
    token_impact = analyzer.analyze_token_impact(df)
    if not token_impact.empty:
        output_path.mkdir(parents=True, exist_ok=True)
        token_impact.to_csv(output_path / "token_impact.csv", index=False)
        print(f"Token impact saved to: {output_path / 'token_impact.csv'}")
    
    # Universal negative
    print("Finding universal negative prompt...")
    universal_negative = analyzer.find_universal_negative(df)
    results['universal_negative'] = universal_negative
    print(f"Universal negative: {universal_negative[:100]}...")
    
    # Redundant tokens
    print("Identifying redundant tokens...")
    redundant_tokens = analyzer.identify_redundant_tokens(df, threshold=0.9)
    if not redundant_tokens.empty:
        redundant_tokens.to_csv(output_path / "redundant_tokens.csv", index=False)
        print(f"Redundant tokens saved to: {output_path / 'redundant_tokens.csv'}")


def cmd_generate_bibles(args):
    """Generate character-specific prompt Bibles."""
    input_path = Path(args.input)
    output_dir = Path(args.output)
    update_markdown = args.update_markdown
    
    # Load CSV
    df = pd.read_csv(input_path)
    
    required_cols = ['positive_prompt', 'character_cluster']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"Error: CSV must contain columns: {missing}")
        sys.exit(1)
    
    generator = PromptBookGenerator()
    base_path = Path("data/Prompts")
    
    # Separate by cluster
    shay_df = df[df['character_cluster'] == 'shay']
    lexie_df = df[df['character_cluster'] == 'lexie']
    universal_df = df[df['character_cluster'] == 'universal']
    
    # Generate character Bibles
    if not shay_df.empty:
        print("Generating Shay Bible...")
        shay_path = output_dir / "Subject-Shay-bible.md"
        generator.generate_character_bible(shay_df, "Shay", shay_path)
        print(f"Saved to: {shay_path}")
    
    if not lexie_df.empty:
        print("Generating Lexie Bible...")
        lexie_path = output_dir / "Subject-Lexie-bible.md"
        generator.generate_character_bible(lexie_df, "Lexie", lexie_path)
        print(f"Saved to: {lexie_path}")
    
    # Generate universal assets
    print("Generating Universal Assets...")
    universal_path = output_dir / "Universal-Assets.md"
    generator.generate_universal_assets(df, universal_path)
    print(f"Saved to: {universal_path}")
    
    # Update existing markdown if requested
    if update_markdown:
        print("Updating existing markdown files...")
        insights = {}  # Could include additional insights here
        generator.update_existing_markdown(shay_df, lexie_df, universal_df, insights, base_path)
        print("Updated existing markdown files in data/Prompts/")


def cmd_full_analysis(args):
    """Run complete analysis pipeline."""
    input_path = Path(args.input)
    output_dir = Path(args.output)
    update_markdown = args.update_markdown
    
    print("=" * 60)
    print("ComfyUI Metadata Full Analysis Pipeline")
    print("=" * 60)
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"\nError: Input path does not exist: {input_path}")
        print(f"Please check the path and try again.")
        print(f"\nTip: If your images are outside the container, you may need to:")
        print(f"  1. Mount the directory into the container")
        print(f"  2. Copy images to the workspace")
        print(f"  3. Run the analysis on the host instead")
        sys.exit(1)
    
    # Setup paths
    shay_path, lexie_path = setup_paths()
    
    # Step 1: Extract metadata
    print("\n[1/5] Extracting metadata...")
    processor = BatchProcessor(
        classify_characters=True,
        decompose_prompts=True,
        shay_md_path=shay_path,
        lexie_md_path=lexie_path
    )
    
    try:
        df = processor.process_directory(
            input_path,
            recursive=args.recursive
        )
        print(f"Extracted {len(df)} records")
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"\nError: {e}")
        sys.exit(1)
    
    if len(df) == 0:
        print("\nWarning: No metadata extracted. Possible reasons:")
        print("  - PNG files don't contain embedded metadata")
        print("  - Files are not ComfyUI-generated images")
        print("  - Metadata was stripped during processing")
    
    # Save intermediate CSV
    intermediate_csv = output_dir / "full_analysis.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(intermediate_csv, index=False)
    print(f"Saved intermediate data to: {intermediate_csv}")
    
    # Step 2: Classification (already done)
    print("\n[2/5] Character classification complete")
    print(df['character_cluster'].value_counts())
    
    # Step 3: Decomposition (already done)
    print("\n[3/5] Prompt decomposition complete")
    
    # Step 4: Template analysis
    print("\n[4/5] Running template analysis...")
    analyzer = TemplateAnalyzer()
    shay_df = df[df['character_cluster'] == 'shay']
    lexie_df = df[df['character_cluster'] == 'lexie']
    
    if not shay_df.empty and not lexie_df.empty:
        common_base = analyzer.find_common_base(shay_df, lexie_df)
        print(f"Common base template identified ({len(common_base)} chars)")
    
    # Step 5: Generate prompt books
    print("\n[5/5] Generating prompt books...")
    generator = PromptBookGenerator()
    
    # Generate Bibles
    if not shay_df.empty:
        generator.generate_character_bible(
            shay_df, "Shay", output_dir / "Subject-Shay-bible.md"
        )
    if not lexie_df.empty:
        generator.generate_character_bible(
            lexie_df, "Lexie", output_dir / "Subject-Lexie-bible.md"
        )
    
    # Generate universal assets
    generator.generate_universal_assets(df, output_dir / "Universal-Assets.md")
    
    # Generate insights report
    generator.generate_insights_report(df, output_dir / "insights_report.md")
    
    # Update existing markdown if requested
    if update_markdown:
        print("Updating existing markdown files...")
        insights = {
            'shay_insights': {},
            'lexie_insights': {}
        }
        generator.update_existing_markdown(
            shay_df, lexie_df, df[df['character_cluster'] == 'universal'],
            insights, Path("data/Prompts")
        )
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print(f"Results saved to: {output_dir}")
    print("=" * 60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ComfyUI Metadata Analyzer - Extract, classify, and analyze image generation metadata"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract metadata from PNG files')
    extract_parser.add_argument('--input', required=True, help='Input directory or file')
    extract_parser.add_argument('--output', required=True, help='Output CSV file')
    extract_parser.add_argument('--recursive', action='store_true', help='Recurse into subdirectories')
    
    # Classify command
    classify_parser = subparsers.add_parser('classify', help='Classify prompts by character')
    classify_parser.add_argument('--input', required=True, help='Input CSV file')
    classify_parser.add_argument('--output', required=True, help='Output CSV file')
    
    # Decompose command
    decompose_parser = subparsers.add_parser('decompose', help='Decompose prompts into components')
    decompose_parser.add_argument('--input', required=True, help='Input CSV file')
    decompose_parser.add_argument('--output', required=True, help='Output CSV file')
    
    # Analyze templates command
    analyze_parser = subparsers.add_parser('analyze-templates', help='Run template analysis')
    analyze_parser.add_argument('--input', required=True, help='Input CSV file')
    analyze_parser.add_argument('--output', help='Output directory (default: same as input)')
    
    # Generate Bibles command
    bibles_parser = subparsers.add_parser('generate-bibles', help='Generate character prompt Bibles')
    bibles_parser.add_argument('--input', required=True, help='Input CSV file')
    bibles_parser.add_argument('--output', required=True, help='Output directory')
    bibles_parser.add_argument('--update-markdown', action='store_true', 
                               help='Update existing markdown files')
    
    # Full analysis command
    full_parser = subparsers.add_parser('full-analysis', help='Run complete analysis pipeline')
    full_parser.add_argument('--input', required=True, help='Input directory')
    full_parser.add_argument('--output', required=True, help='Output directory')
    full_parser.add_argument('--recursive', action='store_true', help='Recurse into subdirectories')
    full_parser.add_argument('--update-markdown', action='store_true',
                            help='Update existing markdown files in data/Prompts/')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command handler
    commands = {
        'extract': cmd_extract,
        'classify': cmd_classify,
        'decompose': cmd_decompose,
        'analyze-templates': cmd_analyze_templates,
        'generate-bibles': cmd_generate_bibles,
        'full-analysis': cmd_full_analysis,
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()

