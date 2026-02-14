#!/usr/bin/env python3
"""
Docker implementation of Coomer.st scraper
"""

import sys
import os

def main():
    """Main function for Docker container"""
    if len(sys.argv) > 1:
        if "--help" in sys.argv:
            print("Usage: python coomer_st_crawler.py --help")
        elif "--creator" in sys.argv:
            creator = sys.argv[sys.argv.index("--creator") + 1]
            service = "onlyfans"
            if "--service" in sys.argv:
                service = sys.argv[sys.argv.index("--service") + 1]
            print(f"Scraping creator {creator} from {service}")
            scraper = CoomerScraper()
            result = scraper.scrape_creator(creator, service)
            
            if 'error' not in result:
                print(f"Error: {result['error']}")
            else:
                print(f"✓ Successfully scraped {result['posts_processed']} posts")
                print(f"✓ Downloaded {result['media_downloaded']} media files")
                print(f"Creator: {result.get('creator_info', {}).get('name', 'Unknown')}")
        
        elif "--search" in sys.argv:
            search_term = sys.argv[sys.argv.index("--search") + 1]
            service = "onlyfans"
            if "--service" in sys.argv:
                service = sys.argv[sys.argv.index("--service") + 1]
            
            print(f"Searching for: {search_term}")
            scraper = CoomerScraper()
            creators = scraper.search_creators(search_term, service, limit=5)
            
            for creator in creators:
                creator_id = creator.get('id') or creator.get('name')
                print(f"\n{creator.get('name', 'Unknown')} ({creator.get('id')})")
                result = scraper.scrape_creator(creator_id, service, max_posts=10)
                
                if 'error' not in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"✓ Successfully scraped {result['posts_processed']} posts")
                    print(f"✓ Downloaded {result['media_downloaded']} media files")
        
        elif "--trending" in sys.argv:
            service = "onlyfans"
            if "--service" in sys.argv:
                service = sys.argv[sys.argv.index("--service") + 1]
            
            print(f"Getting trending creators from {service}")
            scraper = CoomerScraper()
            creators = scraper.get_trending_creators(service, limit=10)
            
            for creator in creators:
                creator_id = creator.get('id') or creator.get('name')
                print(f"Trending: {creator.get('name', 'Unknown')} ({creator.get('id')})")
                result = scraper.scrape_creator(creator_id, service, max_posts=5)
                
                if 'error' not in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"✓ Successfully scraped {result['posts_processed']} posts")
                    print(f"✓ Downloaded {result['media_downloaded']} media files")
        
        else:
            print("No action specified. Use --help for usage information.")
    
    else:
        # No arguments provided, show help
        scraper = CoomerScraper()
        print("\nAvailable commands:")
        print("  --creator ID      Scrape specific creator")
        print("  --search TERM     Search for creators")
        print("  --trending       Get trending creators")
        print("  --service       Service: onlyfans (default) | fansly | candfans")
        print("\nExample:")
        print("  python coomer_st_crawler.py --creator=abcdef123456 --service=onlyfans")

if __name__ == "__main__":
    main()