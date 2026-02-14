"""Run bot pattern analysis on cached data."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.feed.services.bot_pattern_detector import BotPatternDetector


def main():
    """Run analysis on cached imageboard HTML."""
    # Path to cached HTML files
    html_dir = Path("cache/imageboard/html")

    if not html_dir.exists():
        print(f"Error: HTML cache directory not found: {html_dir}")
        return

    print("Initializing bot pattern detector...")
    detector = BotPatternDetector()

    print(f"\nAnalyzing cached HTML files in: {html_dir}")
    print("This may take a few minutes...\n")

    # Run analysis
    results = detector.analyze_cached_html(html_dir)

    # Print report
    detector.print_analysis_report(results)

    # Save detailed results to JSON for further analysis
    import json
    output_file = Path("bot_pattern_analysis_results.json")

    # Convert defaultdict to dict for JSON serialization
    serializable_results = {
        "total_files": results["total_files"],
        "total_posts": results["total_posts"],
        "cross_thread_matches": results["cross_thread_matches"],
        "bot_signatures": dict(results["bot_signatures"]),
        "posting_campaigns": results["posting_campaigns"],
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, default=str)

    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
