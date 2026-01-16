import os
import json
import gzip
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Assuming the runtime environment can resolve these imports
import polars as pl
from minio.error import S3Error

# Assuming existing connections from previous steps
from crawling_system.storage.mysql_repo import MySQLRepository
from crawling_system.storage.minio_store import MinioStore

# Configuration
RAW_BUCKET = "raw-reddit"
DATASET_BUCKET = "datasets"

def fetch_raw_json_from_minio(store: MinioStore, object_name: str) -> Optional[Dict[str, Any]]:
    """Fetches and decompresses a single gzipped JSON object from MinIO."""
    try:
        # Use Boto3 client to download the object
        response = store.get_boto3_client().get_object(Bucket=RAW_BUCKET, Key=object_name)
        compressed_data = response['Body'].read()
        
        # Decompress
        with gzip.open(BytesIO(compressed_data), 'rt', encoding='utf-8') as f:
            return json.load(f)
            
    except S3Error as e:
        print(f"Error fetching object {object_name}: {e}")
        return None
    except Exception as e:
        print(f"General error processing object {object_name}: {e}")
        return None

def run_etl_job(days: int = 7):
    """
    Runs the ETL job:
    1. Queries completed jobs from MySQL for the last `days`.
    2. Downloads raw JSON from MinIO.
    3. Transforms data using Polars.
    4. Saves partitioned Parquet file to MinIO 'datasets' bucket.
    """
    print(f"Starting ETL Job for last {days} days...")
    mysql_repo = MySQLRepository()
    
    # Init store components (We assume minio_store.py handles connection details)
    store = MinioStore()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 1. Get all minio_paths for COMPLETED jobs in the last N days
    # NOTE: This logic assumes we can query minio_path from crawl_jobs table directly.
    # For this MVP, we will simulate this by querying ALL targets and reading ALL files under the relevant date partition.
    
    # Fetch all targets to determine the relevant partitions to scan (more robust in a real S3-style ETL)
    targets = mysql_repo.get_active_targets()
    
    all_data = []
    
    # Simulate scanning MinIO based on date partitions (YYYY/MM/DD)
    date_range = [start_date + timedelta(days=i) for i in range(days)]
    
    for target in targets:
        target_value = target['value']
        for date in date_range:
            date_prefix = f"reddit/{target_value}/{date.strftime('%Y-%m-%d')}/"
            print(f"Scanning MinIO prefix: {date_prefix}...")
            
            # Use Minio client's list_objects to find all files in the partition
            objects = store.client.list_objects(
                RAW_BUCKET, 
                prefix=date_prefix, 
                recursive=True
            )
            
            for obj in objects:
                # 2. Fetch, decompress, and append data
                raw_json = fetch_raw_json_from_minio(store, obj.object_name)
                if raw_json:
                    # 3. Flatten/Extract required fields
                    # We rely on the raw JSON structure being consistent (Reddit Post item)
                    all_data.append({
                        "id": raw_json.get("id"),
                        "subreddit": raw_json.get("subreddit"),
                        "author": raw_json.get("author"),
                        "title": raw_json.get("title"),
                        "selftext": raw_json.get("selftext"),
                        "score": raw_json.get("score"),
                        "upvote_ratio": raw_json.get("upvote_ratio"),
                        "url": raw_json.get("url"),
                        "created_utc": datetime.fromtimestamp(float(raw_json.get("created_utc", 0))),
                        "raw_minio_path": obj.object_name
                    })

    if not all_data:
        print("No raw data collected for this period. Exiting ETL.")
        return

    # 3. Transform using Polars
    df = pl.DataFrame(all_data)
    
    # Add partitioning columns for Hive-style partitioning
    df = df.with_columns([
        df["created_utc"].dt.year().alias("year"),
        df["created_utc"].dt.week().alias("week"),
        pl.lit("reddit").alias("source")
    ])

    # 4. Save Partitioned Parquet to MinIO
    output_prefix = f"datasets/reddit/weekly_archive_{end_date.strftime('%Y_%W')}.parquet"
    print(f"Transformed {len(df)} records. Saving to {DATASET_BUCKET}/{output_prefix}")
    
    # Polars to S3/MinIO
    # Note: Requires a custom S3 writer or writing locally and uploading.
    # For robust S3/Polars integration, `pyarrow` is needed and a temporary local file is safest.
    
    temp_file_path = f"/tmp/weekly_archive_{end_date.strftime('%Y_%W')}.parquet"
    df.write_parquet(temp_file_path)
    
    store.upload_file(DATASET_BUCKET, output_prefix, temp_file_path)
    print(f"Successfully uploaded Parquet dataset: {output_prefix}")
    
    # Clean up local file
    os.remove(temp_file_path)
    
    mysql_repo.close()
    print("ETL Job Finished.")

# Temporary BytesIO import
from io import BytesIO

if __name__ == "__main__":
    run_etl_job(days=7)
