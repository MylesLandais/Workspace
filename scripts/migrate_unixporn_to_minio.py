"""
Script to migrate r/unixporn media from local disk to MinIO and update JSON metadata.
"""
import json
import os
import mimetypes
from pathlib import Path
import subprocess
from minio.error import S3Error
from src.feed.storage.minio_connection import get_minio_connection

# --- Configuration ---
MINIO_PUBLIC_ENDPOINT = "http://localhost:9000"
BUCKET_NAME = "unixporn-media"
OBJECT_PREFIX = "unixporn"
MEDIA_DIR = Path("data") / "media"
DATA_DIR = Path("data")
LATEST_JSON_FILE = DATA_DIR / "unixporn_20260111_174158.json"
OUTPUT_JSON_FILE = DATA_DIR / "unixporn_minio_ready.json"
# ---------------------

def find_latest_json(data_dir: Path) -> Path:
    """Finds the latest unixporn JSON file by name."""
    files = sorted(data_dir.glob("unixporn_*.json"), key=lambda p: p.name, reverse=True)
    if files:
        return files[0]
    raise FileNotFoundError(f"No unixporn JSON files found in {data_dir.absolute()}")

def set_minio_public_policy(bucket_name: str, endpoint: str):
    """
    Attempts to set the MinIO bucket policy to public read using the `mc` client.
    Note: Requires `mc` to be available and configured.
    """
    print(f"   Attempting to set public read policy for {bucket_name}...")
    try:
        # 1. Alias setup (assuming mc isn't pre-aliased, or to refresh it)
        # We use 'minio' as the internal service name as seen in docker-compose files.
        alias_cmd = [
            "mc", "config", "host", "add", "local", f"http://minio:9000",
            "minioadmin", "minioadmin", "--api", "s3v4"
        ]
        subprocess.run(alias_cmd, check=True, capture_output=True, text=True)

        # 2. Set public download policy
        policy_cmd = ["mc", "policy", "set", "download", f"local/{bucket_name}"]
        result = subprocess.run(policy_cmd, check=True, capture_output=True, text=True)
        print(f"   Policy set successfully: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Could not set public policy via mc. MinIO may not be externally accessible.")
        print(f"  Error: {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        print("WARNING: `mc` command not found. Cannot set public policy. Please ensure external access is configured.")
        return False


def migrate_media_to_minio():
    """Migrates media files and updates JSON metadata."""
    print("--- Starting MinIO Migration for r/unixporn ---")
    
    # Initialize MinIO Connection
    minio_conn = get_minio_connection()

    # 1. Ensure Bucket and Set Public Policy
    print(f"1. Ensuring bucket '{BUCKET_NAME}' exists...")
    if not minio_conn.ensure_bucket(BUCKET_NAME):
        print("FATAL: Could not ensure bucket exists. Exiting.")
        return

    # Attempt to set public policy using mc
    set_minio_public_policy(BUCKET_NAME, MINIO_PUBLIC_ENDPOINT)

    # 2. Upload Media Files
    media_files = list(MEDIA_DIR.rglob("*"))
    # Filter out directories and common non-media file types
    media_files = [f for f in media_files if f.is_file() and f.suffix.lower() not in ['.json', '.txt', '.md', '.DS_Store']]
    
    print(f"2. Found {len(media_files)} potential media files to upload from {MEDIA_DIR.absolute()}")
    
    for i, local_path in enumerate(media_files):
        try:
            relative_path = local_path.relative_to(MEDIA_DIR)
            # MinIO object path: unixporn/1pwvpyb.mp4
            object_name = f"{OBJECT_PREFIX}/{relative_path.name}"
            filename = relative_path.name
            
            if minio_conn.object_exists(BUCKET_NAME, object_name):
                print(f"   ({i+1}/{len(media_files)}) Skipping existing: {filename}")
                continue

            content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
            
            print(f"   ({i+1}/{len(media_files)}) Uploading: {filename} as {object_name} (Content-Type: {content_type})...")
            
            if not minio_conn.upload_file(BUCKET_NAME, object_name, str(local_path), content_type=content_type):
                print(f"ERROR: Failed to upload {filename}")
                
        except S3Error as e:
            print(f"MinIO S3 Error for {local_path}: {e}")
        except Exception as e:
            print(f"General error for {local_path}: {e}")

    print("Media upload phase complete.")

    # 3. Update JSON Metadata
    # We use the explicitly found LATEST_JSON_FILE for consistency
    print(f"3. Reading JSON metadata from {LATEST_JSON_FILE}...")
    try:
        with open(LATEST_JSON_FILE, 'r') as f:
            posts = json.load(f)
    except FileNotFoundError:
        print(f"FATAL: Source JSON file not found at {LATEST_JSON_FILE}. Exiting.")
        return

    updated_posts = []
    updated_count = 0
    
    print("4. Updating JSON post entries with new public MinIO URLs...")
    for post in posts:
        # Check for media using the 'local_media_path' key
        if post.get("local_media_path"):
            # Extract filename from the local path. e.g., '1pwvpyb.mp4'
            local_path = Path(post["local_media_path"])
            filename = local_path.name
            
            # Construct the public URL: http://localhost:9000/unixporn-media/unixporn/1pwvpyb.mp4
            media_url = f"{MINIO_PUBLIC_ENDPOINT}/{BUCKET_NAME}/{OBJECT_PREFIX}/{filename}"
            
            # Update the post structure
            post["local_media_path"] = None  # Clear the local path (optional, but good practice)
            post["media_url"] = media_url  # Add the new public media URL
            updated_count += 1
            
        updated_posts.append(post)

    print(f"   Updated {updated_count} posts with MinIO URLs.")

    # 5. Save new JSON metadata
    print(f"5. Saving updated metadata to {OUTPUT_JSON_FILE}...")
    with open(OUTPUT_JSON_FILE, 'w') as f:
        json.dump(updated_posts, f, indent=4)
    
    # 6. Create a symbolic link to make it the latest for consumption
    # Ensure the latest.json symlink points to the new MinIO-ready file
    LATEST_SYMLINK = DATA_DIR / "unixporn_latest.json"
    if LATEST_SYMLINK.exists() or LATEST_SYMLINK.is_symlink():
        os.remove(LATEST_SYMLINK)
    
    os.symlink(OUTPUT_JSON_FILE.name, LATEST_SYMLINK)
    print(f"Created symbolic link: {LATEST_SYMLINK.name} -> {OUTPUT_JSON_FILE.name}")

    print("--- MinIO Migration and JSON Update Complete ---")
    print(f"New data source: {OUTPUT_JSON_FILE.name}")

if __name__ == "__main__":
    # Ensure subprocess is available if needed for mc client
    import sys
    import shutil
    if shutil.which("mc") is None:
        print("Warning: 'mc' client is not found on the path. Public policy cannot be automatically set.")
    
    migrate_media_to_minio()
