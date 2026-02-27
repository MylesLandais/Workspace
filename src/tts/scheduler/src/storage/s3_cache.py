"""
S3-compatible storage cache for images and temporary files.

This module provides utilities for storing cached images and temporary files
in MinIO/S3-compatible storage instead of local filesystem.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime

from ..feed.storage.minio_connection import get_minio_connection


class S3ImageCache:
    """Cache for images stored in S3-compatible storage."""
    
    def __init__(
        self,
        bucket_name: str = "cache",
        prefix: str = "images",
        minio_connection=None
    ):
        """
        Initialize S3 image cache.
        
        Args:
            bucket_name: S3 bucket name for cache
            prefix: Prefix for object keys
            minio_connection: Optional MinIO connection (uses global if None)
        """
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.minio = minio_connection or get_minio_connection()
        
        # Ensure bucket exists
        self.minio.ensure_bucket(bucket_name)
    
    def _get_object_key(self, key: str) -> str:
        """Get full object key with prefix."""
        return f"{self.prefix}/{key}".replace("//", "/")
    
    def store_image(
        self,
        image_data: bytes,
        key: Optional[str] = None,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Store image in S3 cache.
        
        Args:
            image_data: Image bytes
            key: Optional key (auto-generated if None)
            content_type: Content type (default: image/jpeg)
            
        Returns:
            Object key used for storage
        """
        if key is None:
            # Generate key from hash
            hash_obj = hashlib.sha256(image_data)
            key = f"{hash_obj.hexdigest()}.jpg"
        
        object_key = self._get_object_key(key)
        
        if self.minio.upload_bytes(
            self.bucket_name,
            object_key,
            image_data,
            content_type
        ):
            return object_key
        
        raise RuntimeError(f"Failed to upload image to {object_key}")
    
    def get_image_url(self, key: str, expires_seconds: int = 3600) -> Optional[str]:
        """
        Get presigned URL for cached image.
        
        Args:
            key: Object key
            expires_seconds: URL expiration time
            
        Returns:
            Presigned URL or None
        """
        object_key = self._get_object_key(key)
        return self.minio.generate_presigned_url(
            self.bucket_name,
            object_key,
            expires_seconds
        )
    
    def image_exists(self, key: str) -> bool:
        """Check if image exists in cache."""
        object_key = self._get_object_key(key)
        return self.minio.object_exists(self.bucket_name, object_key)
    
    def download_image(self, key: str, file_path: str) -> bool:
        """
        Download cached image to local file.
        
        Args:
            key: Object key
            file_path: Local file path to save to
            
        Returns:
            True if successful
        """
        object_key = self._get_object_key(key)
        return self.minio.download_file(self.bucket_name, object_key, file_path)


class S3TempStorage:
    """Temporary file storage in S3-compatible storage."""
    
    def __init__(
        self,
        bucket_name: str = "temp",
        prefix: str = "files",
        minio_connection=None
    ):
        """
        Initialize S3 temp storage.
        
        Args:
            bucket_name: S3 bucket name for temp files
            prefix: Prefix for object keys
            minio_connection: Optional MinIO connection
        """
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.minio = minio_connection or get_minio_connection()
        
        # Ensure bucket exists
        self.minio.ensure_bucket(bucket_name)
    
    def _get_object_key(self, filename: str, subdir: Optional[str] = None) -> str:
        """Get full object key with prefix and optional subdirectory."""
        if subdir:
            key = f"{self.prefix}/{subdir}/{filename}"
        else:
            key = f"{self.prefix}/{filename}"
        return key.replace("//", "/")
    
    def store_file(
        self,
        file_data: bytes,
        filename: str,
        subdir: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Store temporary file in S3.
        
        Args:
            file_data: File bytes
            filename: Filename
            subdir: Optional subdirectory
            content_type: Content type (auto-detected if None)
            
        Returns:
            Object key used for storage
        """
        object_key = self._get_object_key(filename, subdir)
        
        # Auto-detect content type from extension
        if content_type is None:
            ext = Path(filename).suffix.lower()
            content_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.json': 'application/json',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
            }
            content_type = content_type_map.get(ext, 'application/octet-stream')
        
        if self.minio.upload_bytes(
            self.bucket_name,
            object_key,
            file_data,
            content_type
        ):
            return object_key
        
        raise RuntimeError(f"Failed to upload file to {object_key}")
    
    def store_file_from_path(
        self,
        file_path: str,
        filename: Optional[str] = None,
        subdir: Optional[str] = None
    ) -> str:
        """
        Store file from local path in S3.
        
        Args:
            file_path: Local file path
            filename: Optional filename (uses basename if None)
            subdir: Optional subdirectory
            
        Returns:
            Object key used for storage
        """
        if filename is None:
            filename = Path(file_path).name
        
        object_key = self._get_object_key(filename, subdir)
        
        # Determine content type
        ext = Path(file_path).suffix.lower()
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.json': 'application/json',
            '.txt': 'text/plain',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')
        
        if self.minio.upload_file(
            self.bucket_name,
            object_key,
            file_path,
            content_type
        ):
            return object_key
        
        raise RuntimeError(f"Failed to upload file to {object_key}")
    
    def get_file_url(self, filename: str, subdir: Optional[str] = None, expires_seconds: int = 3600) -> Optional[str]:
        """Get presigned URL for temporary file."""
        object_key = self._get_object_key(filename, subdir)
        return self.minio.generate_presigned_url(
            self.bucket_name,
            object_key,
            expires_seconds
        )
    
    def file_exists(self, filename: str, subdir: Optional[str] = None) -> bool:
        """Check if file exists."""
        object_key = self._get_object_key(filename, subdir)
        return self.minio.object_exists(self.bucket_name, object_key)
    
    def download_file(self, filename: str, file_path: str, subdir: Optional[str] = None) -> bool:
        """Download file from S3 to local path."""
        object_key = self._get_object_key(filename, subdir)
        return self.minio.download_file(self.bucket_name, object_key, file_path)


# Convenience functions
def get_image_cache(bucket_name: str = "cache") -> S3ImageCache:
    """Get image cache instance."""
    return S3ImageCache(bucket_name=bucket_name)


def get_temp_storage(bucket_name: str = "temp") -> S3TempStorage:
    """Get temp storage instance."""
    return S3TempStorage(bucket_name=bucket_name)




