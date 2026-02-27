import os
import sys
import argparse
from pathlib import Path

# Add project root to path for module resolution (necessary in some run environments)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the repository (assuming it resolves in the runtime environment)
from crawling_system.storage.mysql_repo import MySQLRepository

def main():
    parser = argparse.ArgumentParser(description="Add a new target subscription to the Control Plane.")
    parser.add_argument("value", type=str, help="The value of the target (e.g., subreddit name).")
    parser.add_argument("--type", type=str, default="subreddit", help="The type of the target (e.g., subreddit, user, keyword).")
    parser.add_argument("--desc", type=str, default="Test subscription added via CLI.", help="A description for the target.")
    parser.add_argument("--user", type=int, default=1, help="The user ID to subscribe (default: 1).")
    
    args = parser.parse_args()

    repo = MySQLRepository()
    
    print(f"Attempting to add target: Type='{args.type}', Value='{args.value}', User ID={args.user}")
    
    try:
        target_id = repo.add_new_target(
            target_type=args.type,
            value=args.value,
            description=args.desc,
            user_id=args.user
        )
        
        if target_id:
            print(f"\n✓ Successfully added/updated target ID {target_id} and subscribed User {args.user}.")
            print(f"Target '{args.value}' will be picked up by the Producer on the next cycle.")
        else:
            print("\n✗ Failed to add target.")
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        
    finally:
        repo.close()

if __name__ == "__main__":
    main()
