"""Unpack nightly parquet packs from archived data."""

import sys
import os
import tarfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import argparse
import json
import re


def unpack_nightly_pack(
    pack_path: Path,
    output_dir: Optional[Path] = None,
    extract_parquet: bool = True,
    extract_html: bool = False,
    extract_images: bool = False,
) -> Dict[str, Any]:
    """
    Unpack a nightly pack from tarball or directory.
    
    Args:
        pack_path: Path to pack directory or tarball
        output_dir: Output directory for unpacked data (default: unpacked/{pack_name})
        extract_parquet: Extract parquet files to output directory
        extract_html: Extract HTML files from archive
        extract_images: Extract images from archive
    
    Returns:
        Dictionary with pack metadata
    """
    is_tarball = pack_path.suffix in {".tar", ".gz", ".tgz"}
    
    if is_tarball:
        pack_name = pack_path.stem.replace(".tar", "")
        pack_dir = pack_path.parent / pack_name
        temp_dir = pack_path.parent / f"{pack_name}_temp"
    else:
        pack_dir = pack_path
        pack_name = pack_dir.name
        temp_dir = None
    
    if output_dir is None:
        output_dir = Path("unpacked") / pack_name
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print(f"UNPACKING: {pack_name}")
    print("=" * 70)
    print(f"Pack: {pack_path.absolute()}")
    print(f"Output: {output_dir.absolute()}")
    print()
    
    metadata: Dict[str, Any] = {
        "pack_name": pack_name,
        "unpacked_at": datetime.now().isoformat(),
        "source_path": str(pack_path.absolute()),
    }
    
    if is_tarball and temp_dir:
        print("Extracting tarball...")
        try:
            with tarfile.open(pack_path, "r:*") as tar:
                tar.extractall(temp_dir)
            print(f"  Extracted to: {temp_dir}")
        except Exception as e:
            print(f"Error extracting tarball: {e}")
            return metadata
    else:
        temp_dir = pack_dir
    
    metadata_file = temp_dir / "metadata.json"
    if metadata_file.exists():
        print(f"\nReading metadata from {metadata_file}")
        with open(metadata_file, "r", encoding="utf-8") as f:
            pack_metadata = json.load(f)
        metadata.update(pack_metadata)
        
        print(f"  Pack created: {pack_metadata.get('created_at', 'unknown')}")
        print(f"  Threads: {pack_metadata.get('thread_count', 0)}")
        print(f"  Images: {pack_metadata.get('image_count', 0)}")
    
    if extract_parquet:
        print("\nCopying parquet files...")
        parquet_files = list(temp_dir.glob("*.parquet"))
        for parquet_file in parquet_files:
            dest_file = output_dir / parquet_file.name
            shutil.copy2(parquet_file, dest_file)
            print(f"  Copied {parquet_file.name}")
            metadata[f"{parquet_file.stem}_file"] = str(dest_file.relative_to(output_dir))
    
    if extract_html:
        print("\nExtracting HTML files...")
        html_dir = temp_dir / "html"
        if html_dir.exists():
            dest_html_dir = output_dir / "html"
            if dest_html_dir.exists():
                shutil.rmtree(dest_html_dir)
            shutil.copytree(html_dir, dest_html_dir)
            html_count = len(list(dest_html_dir.glob("*.html")))
            print(f"  Extracted {html_count} HTML files")
            metadata["html_dir"] = str(dest_html_dir.relative_to(output_dir))
    
    if extract_images:
        print("\nExtracting images...")
        images_dir = temp_dir / "images"
        if images_dir.exists():
            dest_images_dir = output_dir / "images"
            if dest_images_dir.exists():
                shutil.rmtree(dest_images_dir)
            shutil.copytree(images_dir, dest_images_dir)
            image_count = len(list(dest_images_dir.rglob("*")))
            print(f"  Extracted {image_count} files")
            metadata["images_dir"] = str(dest_images_dir.relative_to(output_dir))
    
    if is_tarball and temp_dir:
        print(f"\nCleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)
    
    print("\n" + "=" * 70)
    print("UNPACK COMPLETE")
    print("=" * 70)
    print(f"\nPack: {pack_name}")
    print(f"Location: {output_dir.absolute()}")
    if extract_parquet:
        parquet_files = list(output_dir.glob("*.parquet"))
        print(f"  Parquet files: {len(parquet_files)}")
    if "html_dir" in metadata:
        html_count = len(list((output_dir / metadata["html_dir"]).glob("*.html")))
        print(f"  HTML files: {html_count}")
    if "images_dir" in metadata:
        image_count = len(list((output_dir / metadata["images_dir"]).rglob("*")))
        print(f"  Image files: {image_count}")
    
    return metadata


def list_packs(packs_dir: Path) -> List[Dict[str, Any]]:
    """List all available packs."""
    packs = []
    
    for pack_path in sorted(packs_dir.glob("nightly-*.tar.gz")) + sorted(packs_dir.glob("nightly-*.tar")):
        pack_name = pack_path.name
        packs.append({
            "name": pack_name,
            "path": str(pack_path.absolute()),
            "size_bytes": pack_path.stat().st_size,
            "size_mb": pack_path.stat().st_size / (1024*1024),
            "modified": datetime.fromtimestamp(pack_path.stat().st_mtime).isoformat(),
        })
    
    for pack_dir in sorted(packs_dir.glob("nightly-*")):
        if pack_dir.is_dir():
            metadata_file = pack_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        pack_metadata = json.load(f)
                    pack_metadata["name"] = pack_dir.name
                    pack_metadata["path"] = str(pack_dir.absolute())
                    packs.append(pack_metadata)
                except Exception as e:
                    print(f"Error reading {metadata_file}: {e}")
    
    return packs


def find_pack_by_timestamp(packs_dir: Path, timestamp: str) -> Optional[Path]:
    """
    Find pack by timestamp string.
    
    Supports:
    - Exact date: "2026-01-02", "2026-01-02T18:00:00"
    - Keywords: "latest", "today", "yesterday"
    - Relative: "3 days ago", "1 week ago"
    - YYYYMMDD: "20260102"
    
    Returns:
        Path to pack tarball or None if not found
    """
    timestamp_lower = timestamp.lower().strip()
    today = datetime.now()
    
    target_date = None
    
    if timestamp_lower == "latest":
        latest_pack = None
        latest_time = None
        
        for pack_path in packs_dir.glob("nightly-*.tar.gz"):
            mtime = datetime.fromtimestamp(pack_path.stat().st_mtime)
            if latest_time is None or mtime > latest_time:
                latest_time = mtime
                latest_pack = pack_path
        
        if latest_pack:
            print(f"Found latest pack: {latest_pack.name}")
            return latest_pack
        
        for pack_path in packs_dir.glob("nightly-*.tar"):
            mtime = datetime.fromtimestamp(pack_path.stat().st_mtime)
            if latest_time is None or mtime > latest_time:
                latest_time = mtime
                latest_pack = pack_path
        
        if latest_pack:
            print(f"Found latest pack: {latest_pack.name}")
            return latest_pack
        
        return None
    
    elif timestamp_lower == "today":
        target_date = today
    
    elif timestamp_lower == "yesterday":
        target_date = today - timedelta(days=1)
    
    elif "ago" in timestamp_lower:
        match = re.match(r"(\d+)\s+(day|week|month)s?\s+ago", timestamp_lower)
        if match:
            num = int(match.group(1))
            unit = match.group(2)
            
            if unit == "day":
                target_date = today - timedelta(days=num)
            elif unit == "week":
                target_date = today - timedelta(weeks=num)
            elif unit == "month":
                target_date = today - timedelta(days=num * 30)
        else:
            return None
    
    else:
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y%m%d",
        ]
        
        for fmt in date_formats:
            try:
                target_date = datetime.strptime(timestamp, fmt)
                break
            except ValueError:
                continue
    
    if target_date is None:
        return None
    
    date_str = target_date.strftime("%Y-%m-%d")
    
    pack_name = f"nightly-{date_str}.tar.gz"
    pack_path = packs_dir / pack_name
    
    if pack_path.exists():
        print(f"Found pack: {pack_path.name}")
        return pack_path
    
    pack_name = f"nightly-{date_str}.tar"
    pack_path = packs_dir / pack_name
    
    if pack_path.exists():
        print(f"Found pack: {pack_path.name}")
        return pack_path
    
    pack_dir = packs_dir / f"nightly-{date_str}"
    if pack_dir.exists():
        print(f"Found pack directory: {pack_dir.name}")
        return pack_dir
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Unpack nightly parquet packs"
    )
    parser.add_argument(
        "pack_spec",
        type=str,
        nargs="?",
        help="Pack path or timestamp (e.g., '2026-01-02', 'latest', 'today', 'yesterday', '3 days ago')"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for unpacked data (default: unpacked/{pack_name})"
    )
    parser.add_argument(
        "--no-parquet",
        action="store_true",
        help="Don't extract parquet files"
    )
    parser.add_argument(
        "--extract-html",
        action="store_true",
        help="Extract HTML files from archive"
    )
    parser.add_argument(
        "--extract-images",
        action="store_true",
        help="Extract images from archive"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available packs instead of unpacking"
    )
    parser.add_argument(
        "--packs-dir",
        type=Path,
        default=Path("packs"),
        help="Directory containing packs (default: packs)"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("=" * 70)
        print("AVAILABLE NIGHTLY PACKS")
        print("=" * 70)
        packs = list_packs(args.packs_dir)
        
        if not packs:
            print("No packs found")
            return
        
        for pack in packs:
            print(f"\n{pack['name']}")
            print(f"  Path: {pack['path']}")
            if "size_mb" in pack:
                print(f"  Size: {pack['size_mb']:.1f} MB")
            if "modified" in pack:
                print(f"  Modified: {pack['modified']}")
            if "thread_count" in pack:
                print(f"  Threads: {pack['thread_count']}")
            if "image_count" in pack:
                print(f"  Images: {pack['image_count']}")
        
        return
    
    pack_path = None
    
    if args.pack_spec:
        pack_spec_path = Path(args.pack_spec)
        
        if pack_spec_path.exists():
            pack_path = pack_spec_path
        else:
            pack_path = find_pack_by_timestamp(args.packs_dir, args.pack_spec)
    
    if pack_path is None:
        parser.error(f"Pack not found: {args.pack_spec}\nUse --list to see available packs or provide a valid path or timestamp")
    
    unpack_nightly_pack(
        pack_path=pack_path,
        output_dir=args.output_dir,
        extract_parquet=not args.no_parquet,
        extract_html=args.extract_html,
        extract_images=args.extract_images,
    )


if __name__ == "__main__":
    sys.exit(main())
