"""
CLI for WD14 tagging service.
Commands: scan, process, status, retry
"""

import click
from typing import Optional
from .wd14_service import WD14Service

service = None


def get_service() -> WD14Service:
    """Lazy initialize service."""
    global service
    if service is None:
        service = WD14Service()
    return service


@click.group()
def wd14():
    """WD14 image tagging pipeline."""
    pass


@wd14.command()
@click.option("--bucket", required=True, help="S3 bucket to scan")
@click.option("--prefix", default="", help="S3 prefix filter")
def scan(bucket: str, prefix: str):
    """Discover images in S3 bucket.

    Scans bucket and registers new images for processing.
    Skips already-tagged images.
    """
    try:
        service = get_service()
        images, new_count = service.scan_bucket(bucket, prefix)

        click.echo(f"Found {len(images)} images, {new_count} new")
        click.echo(f"Bucket: {bucket}")
        if prefix:
            click.echo(f"Prefix: {prefix}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


@wd14.command()
@click.option("--bucket", required=True, help="S3 bucket to process")
@click.option("--prefix", default="", help="S3 prefix filter")
@click.option("--limit", type=int, default=None, help="Max images to process")
@click.option("--batch-size", type=int, default=32, help="Batch size (WD14 tagger)")
def process(bucket: str, prefix: str, limit: Optional[int], batch_size: int):
    """Process images with WD14 tagger.

    Downloads images from S3, runs WD14 inference, caches results.
    Uses local CUDA GPU (8GB VRAM).
    """
    try:
        service = get_service()
        service.tagger.config.batch_size = batch_size

        # Scan first
        click.echo(f"Scanning {bucket}...")
        images, new_count = service.scan_bucket(bucket, prefix)

        if new_count == 0:
            click.echo("No new images to process")
            return

        # Process batch
        click.echo(f"Processing {new_count} images...")
        stats = service.process_batch(images, limit)

        click.echo(f"Results: {stats['success']} success, {stats['failed']} failed")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


@wd14.command()
def status():
    """Show tagging status and cache statistics."""
    try:
        service = get_service()
        stats = service.get_stats()

        click.echo("WD14 Cache Status")
        click.echo(f"  Cached tags: {stats['cached_tags']}")
        click.echo(f"  Failed jobs: {stats['failed_jobs']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


@wd14.command()
@click.option("--older-than", type=int, default=24, help="Hours (retry jobs failed longer ago)")
def retry(older_than: int):
    """Retry failed tagging jobs.

    Retags images that failed earlier (older than --older-than hours).
    """
    try:
        service = get_service()

        click.echo(f"Retrying jobs failed > {older_than} hours ago...")
        stats = service.retry_failed(older_than_hours=older_than)

        click.echo(f"Retried: {stats['retried']}")
        click.echo(f"  Success: {stats['success']}")
        click.echo(f"  Failed: {stats['failed']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


@wd14.command()
@click.argument("image_sha256")
def tags(image_sha256: str):
    """Get cached tags for image by SHA256."""
    try:
        service = get_service()
        result = service.get_tags(image_sha256)

        if not result:
            click.echo(f"No tags found for {image_sha256}")
            return

        click.echo(f"Image: {image_sha256}")
        click.echo(f"Rating: {result.rating}")
        click.echo(f"Model: {result.model_version}")
        click.echo(f"Processed: {result.processed_at}")

        if result.character_tags:
            click.echo("\nCharacter Tags:")
            for tag in result.character_tags:
                click.echo(f"  {tag.name}: {tag.confidence:.2%}")

        if result.general_tags:
            click.echo("\nGeneral Tags:")
            for tag in result.general_tags[:20]:  # Show top 20
                click.echo(f"  {tag.name}: {tag.confidence:.2%}")
            if len(result.general_tags) > 20:
                click.echo(f"  ... and {len(result.general_tags) - 20} more")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


if __name__ == "__main__":
    wd14()
