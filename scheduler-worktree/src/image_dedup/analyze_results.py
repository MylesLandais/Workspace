"""Analyze duplicate detection results from the database."""

import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from feed.storage.neo4j_connection import get_connection
from image_dedup import ImageAnalytics, ImageQueries


def print_separator():
    """Print a separator line."""
    print("\n" + "=" * 80 + "\n")


def main():
    """Analyze and display duplicate detection results."""
    neo4j = get_connection()
    analytics = ImageAnalytics()
    queries = ImageQueries()

    print_separator()
    print("IMAGE DEDUPLICATION RESULTS ANALYSIS")
    print_separator()

    # 1. Overall Statistics
    print("1. OVERALL STATISTICS")
    print("-" * 80)
    total_stats = analytics.get_total_statistics()
    
    print(f"Total Images Processed: {total_stats['total_images']:,}")
    print(f"Total Clusters: {total_stats['total_clusters']:,}")
    print(f"Total Reposts Detected: {total_stats['total_reposts']:,}")
    print(f"Total Posts: {total_stats['total_posts']:,}")
    print(f"Clusters with Reposts: {total_stats['clusters_with_reposts']:,}")
    print(f"Overall Repost Rate: {total_stats['overall_repost_rate']:.2%}")

    # 2. Most Reposted Images
    print_separator()
    print("2. TOP 20 MOST REPOSTED IMAGES")
    print("-" * 80)
    
    top_reposts = analytics.get_most_reposted_images(limit=20, min_reposts=2)
    
    if not top_reposts:
        print("No reposted images found yet. Run batch processing to populate data.")
    else:
        print(f"{'Rank':<6} {'Reposts':<8} {'Cluster ID':<40} {'First Subreddit':<20}")
        print("-" * 80)
        for i, repost in enumerate(top_reposts[:20], 1):
            cluster_id = repost['cluster_id'][:36] + "..." if len(repost['cluster_id']) > 36 else repost['cluster_id']
            subreddit = repost.get('first_subreddit', 'N/A') or 'N/A'
            if len(subreddit) > 18:
                subreddit = subreddit[:15] + "..."
            print(f"{i:<6} {repost['repost_count']:<8} {cluster_id:<40} {subreddit:<20}")

    # 3. Cluster Size Distribution
    print_separator()
    print("3. CLUSTER SIZE DISTRIBUTION")
    print("-" * 80)
    
    distribution = analytics.get_cluster_size_distribution()
    
    if not distribution:
        print("No clusters found. Run batch processing to populate data.")
    else:
        print(f"{'Cluster Size':<15} {'Count':<10} {'Percentage':<15}")
        print("-" * 40)
        
        total_clusters = sum(distribution.values())
        sorted_sizes = sorted([(int(k), v) for k, v in distribution.items()], reverse=True)
        
        for size, count in sorted_sizes[:15]:
            percentage = (count / total_clusters * 100) if total_clusters > 0 else 0
            print(f"{size:<15} {count:<10} {percentage:>6.2f}%")

    # 4. Daily Statistics
    print_separator()
    print("4. RECENT DAILY STATISTICS")
    print("-" * 80)
    
    from datetime import timedelta
    today = datetime.utcnow()
    
    print(f"{'Date':<12} {'Ingested':<12} {'Duplicates':<12} {'New Clusters':<15} {'Dup Rate':<12}")
    print("-" * 80)
    
    for days_ago in range(7):
        date = today - timedelta(days=days_ago)
        daily_stats = analytics.get_daily_statistics(date)
        
        date_str = daily_stats['date']
        ingested = daily_stats['images_ingested']
        duplicates = daily_stats['duplicates_detected']
        new_clusters = daily_stats['new_clusters']
        dup_rate = daily_stats['duplicate_rate']
        
        print(f"{date_str:<12} {ingested:<12} {duplicates:<12} {new_clusters:<15} {dup_rate:>10.2%}")

    # 5. Subreddit Statistics
    print_separator()
    print("5. TOP 10 SUBREDDITS BY REPOST RATE")
    print("-" * 80)
    
    subreddit_stats = analytics.get_subreddit_statistics(limit=10)
    
    if not subreddit_stats:
        print("No subreddit statistics available.")
    else:
        print(f"{'Subreddit':<25} {'Total Images':<15} {'Reposts':<12} {'Repost Rate':<15}")
        print("-" * 80)
        
        for stats in subreddit_stats[:10]:
            subreddit = stats['subreddit'] or 'N/A'
            if len(subreddit) > 23:
                subreddit = subreddit[:20] + "..."
            print(f"{subreddit:<25} {stats['total_images']:<15} {stats['reposted_images']:<12} {stats['repost_rate']:>13.2%}")

    # 6. Sample Cluster Details
    print_separator()
    print("6. SAMPLE CLUSTER DETAILS (Top Reposted)")
    print("-" * 80)
    
    if top_reposts:
        sample = top_reposts[0]
        cluster_id = sample['cluster_id']
        cluster_info = queries.get_cluster_info(cluster_id, include_members=True, member_limit=5)
        
        if cluster_info:
            print(f"Cluster ID: {cluster_info.cluster_id}")
            print(f"Repost Count: {cluster_info.repost_count}")
            print(f"Member Count: {cluster_info.member_count}")
            print(f"First Seen: {cluster_info.first_seen}")
            print(f"Last Seen: {cluster_info.last_seen}")
            
            if cluster_info.members:
                print(f"\nSample Members ({len(cluster_info.members)} shown):")
                for i, member in enumerate(cluster_info.members[:5], 1):
                    print(f"  {i}. Image ID: {member.image_id[:36]}...")
                    print(f"     Posts: {len(member.post_ids)}")
                    if member.post_ids:
                        print(f"     First Post: {member.post_ids[0]}")

    # 7. Duplicate Detection Methods
    print_separator()
    print("7. DUPLICATE DETECTION METHODS")
    print("-" * 80)
    
    query = """
    MATCH (i:ImageFile)-[r:REPOST_OF]->(original:ImageFile)
    WITH r.detected_method as method, count(*) as count
    RETURN method, count
    ORDER BY count DESC
    """
    
    result = neo4j.execute_read(query)
    
    if not result:
        print("No repost relationships found yet.")
    else:
        print(f"{'Method':<20} {'Count':<10}")
        print("-" * 30)
        for record in result:
            method = record.get('method') or 'unknown'
            count = record.get('count', 0)
            print(f"{method:<20} {count:<10}")

    print_separator()
    print("Analysis complete!")
    print_separator()


if __name__ == "__main__":
    main()







