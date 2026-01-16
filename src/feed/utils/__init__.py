"""Utility functions for feed engine."""

from .image_filter import is_image_url, filter_image_posts
from .image_hash import (
    compute_sha256_hash,
    compute_dhash,
    download_and_hash_image,
    hash_image_url,
)

try:
    from .image_checker import (
        check_image_by_url,
        check_image_by_hash,
        get_image_statistics,
    )
    __all__ = [
        "is_image_url",
        "filter_image_posts",
        "compute_sha256_hash",
        "compute_dhash",
        "download_and_hash_image",
        "hash_image_url",
        "check_image_by_url",
        "check_image_by_hash",
        "get_image_statistics",
    ]
except ImportError:
    __all__ = [
        "is_image_url",
        "filter_image_posts",
        "compute_sha256_hash",
        "compute_dhash",
        "download_and_hash_image",
        "hash_image_url",
    ]

