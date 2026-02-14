"""Check thread relationships in Neo4j."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def main():
    print("=" * 70)
    print("THREAD RELATIONSHIPS")
    print("=" * 70)
    
    conn = get_connection()
    
    # Get all thread relationships
    result = conn.execute_read(
        """
        MATCH (t1:Thread)-[r:CONTINUES_TO]->(t2:Thread)
        RETURN t1.board as from_board, 
               t1.thread_id as from_thread,
               t2.board as to_board,
               t2.thread_id as to_thread,
               r.created_at as created
        ORDER BY r.created_at DESC
        LIMIT 20
        """
    )
    
    if result:
        print(f"\nFound {len(result)} thread relationship(s):\n")
        for record in result:
            from_board = record["from_board"]
            from_thread = record["from_thread"]
            to_board = record["to_board"]
            to_thread = record["to_thread"]
            created = record.get("created", "N/A")
            print(f"  /{from_board}/{from_thread} -> /{to_board}/{to_thread}")
            print(f"    Created: {created}")
    else:
        print("\nNo thread relationships found.")
    
    # Get thread chain (follow relationships)
    print("\n" + "=" * 70)
    print("THREAD CHAINS")
    print("=" * 70)
    
    result2 = conn.execute_read(
        """
        MATCH path = (start:Thread)-[:CONTINUES_TO*]->(end:Thread)
        WHERE NOT (end)-[:CONTINUES_TO]->()
        RETURN start.board as start_board,
               start.thread_id as start_thread,
               end.board as end_board,
               end.thread_id as end_thread,
               length(path) as chain_length
        ORDER BY chain_length DESC
        LIMIT 10
        """
    )
    
    if result2:
        print(f"\nFound {len(result2)} thread chain(s):\n")
        for record in result2:
            start_board = record["start_board"]
            start_thread = record["start_thread"]
            end_board = record["end_board"]
            end_thread = record["end_thread"]
            chain_length = record["chain_length"]
            print(f"  Chain length {chain_length}: /{start_board}/{start_thread} -> ... -> /{end_board}/{end_thread}")
    else:
        print("\nNo thread chains found.")
    
    conn.close()
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()






