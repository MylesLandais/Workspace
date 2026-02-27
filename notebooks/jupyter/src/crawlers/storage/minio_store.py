import json
import gzip
import os
from datetime import datetime
from io import BytesIO
from typing import Dict, Any
from minio import Minio
from ..core.interfaces import ObjectStore

class MinioStore(ObjectStore):
    """
    Stores raw data in MinIO/S3.
    """

    def __init__(self, endpoint: str = None, access_key: str = None, secret_key: str = None, secure: bool = False, bucket: str = "raw-data"):
        if endpoint is None:
            endpoint = os.environ.get("S3_ENDPOINT", os.environ.get("MINIO_ENDPOINT", "localhost:8333"))
        if access_key is None:
            access_key = os.environ.get("S3_ACCESS_KEY", os.environ.get("MINIO_ACCESS_KEY", "admin"))
        if secret_key is None:
            secret_key = os.environ.get("S3_SECRET_KEY", os.environ.get("MINIO_SECRET_KEY", "password"))
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket = bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def save_raw(self, data: Dict[str, Any], path: str) -> str:
        """
        Saves data as a compressed JSON file.
        
        Args:
            data: The data dict.
            path: The logical path (e.g., "reddit/nixos/2023-10-27/post_id.json")
            
        Returns:
            The actual object key used.
        """
        # Serialize and Compress
        json_bytes = json.dumps(data).encode('utf-8')
        # We can optionally gzip here. For raw storage, gzip is good.
        # But for simplicity in the MVP, let's store plain JSON or do simple gzip.
        # Let's do gzip.
        
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
            f.write(json_bytes)
        buffer.seek(0)
        
        # Append .gz if not present
        if not path.endswith('.gz'):
            path += '.gz'
            
        # Upload
        self.client.put_object(
            self.bucket,
            path,
            buffer,
            length=buffer.getbuffer().nbytes,
            content_type="application/json"
        )
        
        return path
