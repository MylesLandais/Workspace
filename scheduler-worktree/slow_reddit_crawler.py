#!/usr/bin/env python3
"""Slow Reddit crawler for monitoring 100 subreddits with random delays."""

import sys
import time
import random
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.polling.engine import PollingEngine
from feed.storage.neo4j_connection import get_connection


# 100 subreddits to monitor
SUBREDDITS = [
    "AddisonRae",
    "BotezLive",
    "HannahBeast",
    "OfflinetvGirls",
    "Taylorhillfantasy",
    "SommerRay",
    "kendalljenner",
    "popheadscirclejerk",
    "WhatAWeeb",
    "ArianaGrande",
    "KatrinaBowden",
    "KiraKosarin",
    "KiraKosarinLewd",
    "LeightonMeester",
    "MargotRobbie",
    "MarinKitagawaR34",
    "McKaylaMaroney",
    "MelissaBenoist",
    "MinkaKelly",
    "MirandaKerr",
    "Models",
    "NatalieDormer",
    "NinaDobrev",
    "Nina_Agdal",
    "OfflinetvGirls",
    "OliviaRodrigoNSFW",
    "OneTrueMentalOut",
    "OvileeWorship",
    "PhoebeTonkin",
    "Pokimane",
    "PortiaDoubleday",
    "RachelCook",
    "RachelMcAdams",
    "SammiHanratty",
    "SaraSampaio",
    "SarahHyland",
    "SelenaGomez",
    "ShaileneWoodley",
    "StellaMaxwell",
    "SydneySweeney",
    "TOS_girls",
    "TaylorSwift",
    "TaylorSwiftCandids",
    "TaylorSwiftMidriff",
    "Taylorhillfantasy",
    "VanessaHudgens",
    "VolleyballGirls",
    "WatchItForThePlot",
    "angourierice",
    "annakendrick",
    "blakelively",
    "candiceswanepoel",
    "erinmoriartyNEW",
    "haydenpanettiere",
    "howdyhowdyyallhot",
    "islafisher",
    "jenniferlovehewitt",
    "jessicaalba",
    "karliekloss",
    "kateupton",
    "kayascodelario",
    "kristenbell",
    "kristinefroseth",
    "lizgillies",
    "milanavayntrub",
    "natalieportman",
    "oliviadunne",
    "sophieturner",
    "sunisalee",
    "victoriajustice",
    "victorious",
    "vsangels",
    "JennaOrtega",
    "lululemon",
    "tspics",
    "SonoBisqueDoll",
]

# Remove duplicates while preserving order
SUBREDDITS = list(dict.fromkeys(SUBREDDITS))

# Very slow delay settings (in seconds)
# Between requests within a subreddit
REQUEST_DELAY_MIN = 10.0
REQUEST_DELAY_MAX = 30.0

# Between subreddits
SUBREDDIT_DELAY_MIN = 60.0
SUBREDDIT_DELAY_MAX = 180.0

# Between cycles (after completing all subreddits)
CYCLE_DELAY_MIN = 300.0
CYCLE_DELAY_MAX = 600.0

# Between steps (before/after operations)
STEP_DELAY_MIN = 5.0
STEP_DELAY_MAX = 15.0


def random_delay(min_sec: float, max_sec: float, reason: str = ""):
    """Sleep for a random duration and log it."""
    delay = random.uniform(min_sec, max_sec)
    if reason:
        print(f"  [DELAY] {reason}: {delay:.1f} seconds")
    time.sleep(delay)


def main():
    """Main crawler loop."""
    print("=" * 80)
    print("SLOW REDDIT CRAWLER - 100 Subreddits")
    print("=" * 80)
    print(f"Total subreddits: {len(SUBREDDITS)}")
    print(f"Request delays: {REQUEST_DELAY_MIN}-{REQUEST_DELAY_MAX} seconds")
    print(f"Subreddit delays: {SUBREDDIT_DELAY_MIN}-{SUBREDDIT_DELAY_MAX} seconds")
    print(f"Cycle delays: {CYCLE_DELAY_MIN}-{CYCLE_DELAY_MAX} seconds")
    print("=" * 80)
    print()
    
    # Initialize Reddit adapter with slow delays
    reddit = RedditAdapter(
        mock=False,
        delay_min=REQUEST_DELAY_MIN,
        delay_max=REQUEST_DELAY_MAX,
    )
    
    # Initialize Neo4j connection
    try:
        neo4j = get_connection()
        print(f"Connected to Neo4j: {neo4j.uri}")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        print("Make sure NEO4J_URI and NEO4J_PASSWORD are set in .env")
        return 1
    
    # Run migration if needed
    try:
        migration_path = Path(__file__).parent / "src" / "feed" / "storage" / "migrations" / "001_initial_schema.cypher"
        if migration_path.exists():
            with open(migration_path) as f:
                migration = f.read()
            statements = [s.strip() for s in migration.split(";") if s.strip()]
            for stmt in statements:
                if stmt:
                    try:
                        neo4j.execute_write(stmt)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            pass
    except Exception:
        pass
    
    # Initialize polling engine
    engine = PollingEngine(reddit, neo4j, dry_run=False)
    
    cycle = 0
    
    try:
        while True:
            cycle += 1
            print()
            print("=" * 80)
            print(f"CYCLE {cycle} - Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            print()
            
            random_delay(STEP_DELAY_MIN, STEP_DELAY_MAX, "Pre-cycle delay")
            
            for idx, subreddit in enumerate(SUBREDDITS, 1):
                print()
                print("-" * 80)
                print(f"[{idx}/{len(SUBREDDITS)}] Processing r/{subreddit}")
                print("-" * 80)
                
                random_delay(STEP_DELAY_MIN, STEP_DELAY_MAX, "Pre-subreddit delay")
                
                try:
                    # Poll the subreddit (only fetch first page to be slow)
                    posts = engine.poll_source(
                        source=subreddit,
                        sort="new",
                        max_pages=1,
                        limit_per_page=100,
                    )
                    
                    print(f"  Collected {len(posts)} posts from r/{subreddit}")
                    
                except Exception as e:
                    print(f"  ERROR processing r/{subreddit}: {e}")
                    # Continue to next subreddit even on error
                
                # Delay between subreddits
                if idx < len(SUBREDDITS):
                    random_delay(SUBREDDIT_DELAY_MIN, SUBREDDIT_DELAY_MAX, f"Between subreddits (next: r/{SUBREDDITS[idx]})")
            
            # Delay between cycles
            print()
            print("=" * 80)
            print(f"Cycle {cycle} complete. All {len(SUBREDDITS)} subreddits processed.")
            print(f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
            random_delay(CYCLE_DELAY_MIN, CYCLE_DELAY_MAX, "Between cycles")
            
    except KeyboardInterrupt:
        print()
        print("=" * 80)
        print("Crawler stopped by user")
        print(f"Completed {cycle} cycle(s)")
        print("=" * 80)
        return 0
    except Exception as e:
        print()
        print("=" * 80)
        print(f"FATAL ERROR: {e}")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())








