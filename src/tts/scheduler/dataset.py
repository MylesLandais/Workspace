"""
Command-Line Interface for Dataset Management
"""
import argparse
from pathlib import Path
from src.datasets.manager import DatasetManager

def main():
    parser = argparse.ArgumentParser(description="Dataset Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- List Command ---
    subparsers.add_parser("list", help="List all available datasets.")

    # --- Info Command ---
    info_parser = subparsers.add_parser("info", help="Get information about a specific dataset.")
    info_parser.add_argument("name", type=str, help="The name of the dataset.")

    # --- Get Command ---
    get_parser = subparsers.add_parser("get", help="Download or verify a dataset.")
    get_parser.add_argument("name", type=str, help="The name of the dataset to get.")
    get_parser.add_argument(
        "--path",
        type=str,
        default="evaluation_datasets",
        help="The destination directory for the dataset."
    )

    args = parser.parse_args()
    manager = DatasetManager()

    if args.command == "list":
        print("Available datasets:")
        for name in manager.list_datasets():
            print(f"- {name}")

    elif args.command == "info":
        handler = manager.get_handler(args.name)
        if handler:
            print(f"--- Info for '{args.name}' ---")
            for key, value in handler.info().items():
                print(f"{key.capitalize()}: {value}")
        else:
            print(f"Error: Dataset '{args.name}' not found.")

    elif args.command == "get":
        handler = manager.get_handler(args.name)
        if handler:
            print(f"--- Getting dataset '{args.name}' ---")
            try:
                dataset_path = handler.get(Path(args.path))
                print(f"\nDataset is available at: {dataset_path.resolve()}")
            except Exception as e:
                print(f"\nAn error occurred: {e}")
        else:
            print(f"Error: Dataset '{args.name}' not found.")

if __name__ == "__main__":
    main()
