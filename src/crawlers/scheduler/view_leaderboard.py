#!/usr/bin/env python3
"""
View ASR Model Leaderboard from PostgreSQL Database
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from asr_evaluation.storage.postgres_storage import PostgreSQLStorage


def print_leaderboard(results: List[Dict[str, Any]]):
    """Print formatted leaderboard."""
    print("\n" + "="*120)
    print("ASR MODEL LEADERBOARD - VAPOREON COPYPASTA DATASET")
    print("="*120)
    
    if not results:
        print("No results found in database!")
        return
    
    # Print header
    print(f"{'Rank':<4} {'Model':<25} {'Version':<15} {'Type':<8} {'Avg WER':<8} {'Best WER':<8} {'Avg CER':<8} {'Evals':<6} {'Avg Time':<8} {'Last Run'}")
    print("-" * 120)
    
    # Print results
    for i, result in enumerate(results, 1):
        model_name = result["model_name"][:24]
        version = result["model_version"][:14] if result["model_version"] else "N/A"
        model_type = result["model_type"][:7] if result["model_type"] else "N/A"
        avg_wer = f"{result['avg_wer']:.2%}" if result['avg_wer'] is not None else "N/A"
        best_wer = f"{result['best_wer']:.2%}" if result['best_wer'] is not None else "N/A"
        avg_cer = f"{result['avg_cer']:.2%}" if result['avg_cer'] is not None else "N/A"
        eval_count = str(result["evaluation_count"])
        avg_time = f"{result['avg_processing_time']:.1f}s" if result['avg_processing_time'] is not None else "N/A"
        last_run = result["last_evaluation"].strftime("%m/%d %H:%M") if result["last_evaluation"] else "N/A"
        
        print(f"{i:<4} {model_name:<25} {version:<15} {model_type:<8} {avg_wer:<8} {best_wer:<8} {avg_cer:<8} {eval_count:<6} {avg_time:<8} {last_run}")


def print_model_details(storage: PostgreSQLStorage, model_name: str):
    """Print detailed history for a specific model."""
    history = storage.get_model_history(model_name)
    
    if not history:
        print(f"No history found for model: {model_name}")
        return
    
    print(f"\n" + "="*80)
    print(f"MODEL HISTORY: {model_name}")
    print("="*80)
    
    print(f"{'Date':<12} {'Experiment':<25} {'WER':<8} {'CER':<8} {'Time':<8} {'Words'}")
    print("-" * 80)
    
    for result in history:
        date = result["created_at"].strftime("%m/%d %H:%M")
        experiment = result["experiment_name"][:24] if result["experiment_name"] else "N/A"
        wer = f"{result['wer']:.2%}" if result['wer'] is not None else "N/A"
        cer = f"{result['cer']:.2%}" if result['cer'] is not None else "N/A"
        time_val = f"{result['processing_time']:.1f}s" if result['processing_time'] is not None else "N/A"
        words = len(result['predicted_text'].split()) if result['predicted_text'] else 0
        
        print(f"{date:<12} {experiment:<25} {wer:<8} {cer:<8} {time_val:<8} {words}")


def print_dataset_stats(storage: PostgreSQLStorage, dataset_name: str = "vaporeon_copypasta"):
    """Print dataset statistics."""
    stats = storage.get_dataset_stats(dataset_name)
    
    if not stats:
        print(f"No statistics found for dataset: {dataset_name}")
        return
    
    print(f"\n" + "="*60)
    print(f"DATASET STATISTICS: {dataset_name}")
    print("="*60)
    
    print(f"Total Evaluations: {stats.get('total_evaluations', 0)}")
    print(f"Unique Models: {stats.get('unique_models', 0)}")
    print(f"Average WER: {stats.get('avg_wer', 0):.2%}")
    print(f"Best WER: {stats.get('best_wer', 0):.2%}")
    print(f"Worst WER: {stats.get('worst_wer', 0):.2%}")
    print(f"Average Processing Time: {stats.get('avg_processing_time', 0):.2f}s")


def main():
    """Main function."""
    print("ASR Model Leaderboard Viewer")
    
    # Initialize storage
    try:
        storage = PostgreSQLStorage()
        print("Connected to PostgreSQL database")
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        print("Make sure PostgreSQL is running and accessible")
        return
    
    # Get command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "model" and len(sys.argv) > 2:
            model_name = sys.argv[2]
            print_model_details(storage, model_name)
        elif command == "stats":
            dataset_name = sys.argv[2] if len(sys.argv) > 2 else "vaporeon_copypasta"
            print_dataset_stats(storage, dataset_name)
        else:
            print("Usage:")
            print("  python view_leaderboard.py                    # Show leaderboard")
            print("  python view_leaderboard.py model <name>       # Show model history")
            print("  python view_leaderboard.py stats [dataset]    # Show dataset stats")
            return
    else:
        # Show leaderboard
        leaderboard = storage.get_leaderboard(dataset_name="vaporeon_copypasta")
        print_leaderboard(leaderboard)
        
        # Show quick stats
        print_dataset_stats(storage)
    
    storage.close()


if __name__ == "__main__":
    main()