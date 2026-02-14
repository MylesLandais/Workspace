#!/usr/bin/env python3
"""
Generates a Hugging Face / Kaggle compatible Parquet dataset.
Embeds image bytes into the Parquet file for instant browser viewing
on platforms like Hugging Face Dataset Viewer.
"""
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime

# Paths
PACK_BASE_DIR = Path('/home/warby/Workspace/jupyter/packs')
# Find the latest archive directory (ignore the .tar.gz files)
LATEST_DIR = sorted([d for d in PACK_BASE_DIR.glob('imageboard_full_archive_*') if d.is_dir()], key=os.path.getmtime)[-1]
INDEX_PARQUET = LATEST_DIR / "dataset_index.parquet"
IMAGES_DIR = LATEST_DIR / "images"
OUTPUT_PARQUET = LATEST_DIR / "huggingface_dataset.parquet"

def create_hf_dataset():
    print(f"Loading index from {INDEX_PARQUET}...")
    df = pd.read_parquet(INDEX_PARQUET)
    
    # We'll create a list for the image bytes
    image_bytes_list = []
    
    print(f"Embedding image bytes for {len(df)} entries...")
    for idx, row in df.iterrows():
        rel_path = row.get('image_rel_path')
        img_data = None
        if rel_path:
            full_path = LATEST_DIR / rel_path
            if full_path.exists():
                try:
                    with open(full_path, 'rb') as f:
                        img_data = f.read()
                except Exception as e:
                    print(f"Error reading {full_path}: {e}")
        
        image_bytes_list.append(img_data)
        
        if idx > 0 and idx % 1000 == 0:
            print(f"  Processed {idx} rows...")

    # Add the bytes column
    # HF Dataset viewer looks for a column named 'image' containing bytes
    df['image'] = image_bytes_list
    
    # Rename columns to standard HF names if they exist
    # 'comment' -> 'text'
    if 'comment' in df.columns:
        df = df.rename(columns={'comment': 'text'})
    
    # Drop rows without images if desired, or keep them
    # For a 'viewer' experience, rows with images are best
    print(f"Final dataset has {len(df)} rows.")
    
    # Convert to PyArrow Table
    table = pa.Table.from_pandas(df)
    
    print(f"Writing to {OUTPUT_PARQUET}...")
    pq.write_table(table, OUTPUT_PARQUET, compression='snappy')
    
    print("=" * 70)
    print("HUGGING FACE COMPATIBLE DATASET CREATED")
    print(f"Location: {OUTPUT_PARQUET}")
    print(f"Size: {os.path.getsize(OUTPUT_PARQUET) / (1024*1024):.1f} MB")
    print("=" * 70)
    print("Tip: Upload this Parquet to a Hugging Face Dataset repository")
    print("and the 'image' column will automatically render in the browser.")

if __name__ == "__main__":
    create_hf_dataset()
