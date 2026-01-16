"""MinIO/S3-compatible object storage connection management."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error
from botocore.config import Config


class MinIOConnection:
    """Manages MinIO/S3-compatible object storage connections."""

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize MinIO connection.
        
        Args:
            env_path: Path to .env file. Defaults to ~/workspace/.env
        """
        # Support both Docker container and local development
        if env_path:
            self.env_path = env_path
        elif Path("/home/jovyan/workspaces/.env").exists():
            self.env_path = Path("/home/jovyan/workspaces/.env")
        elif Path(".env").exists():
            self.env_path = Path(".env").absolute()
        else:
            self.env_path = Path.home() / "Workspace" / "jupyter" / ".env"
        self._load_environment()
        
        # MinIO/S3 configuration
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.region = os.getenv("MINIO_REGION", "us-east-1")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        # Ensure endpoint has protocol prefix
        if not self.endpoint.startswith(("http://", "https://")):
            self.endpoint = f"http://{self.endpoint}"
            if self.secure:
                self.endpoint = f"https://{self.endpoint}"
        
        self._minio_client: Optional[Minio] = None
        self._boto3_client: Optional[boto3.client] = None

    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        load_dotenv(self.env_path, override=True)

    def get_minio_client(self) -> Minio:
        """
        Get MinIO client instance.
        
        Returns:
            MinIO client instance
        """
        if self._minio_client is None:
            self._minio_client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
        return self._minio_client

    def get_boto3_client(self):
        """
        Get boto3 S3 client (for S3-compatible operations).
        
        Returns:
            boto3 S3 client
        """
        if self._boto3_client is None:
            self._boto3_client = boto3.client(
                "s3",
                endpoint_url=f"{'https' if self.secure else 'http'}://{self.endpoint}",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(signature_version="s3v4"),
            )
        return self._boto3_client

    def ensure_bucket(self, bucket_name: str) -> bool:
        """
        Ensure bucket exists, creating it if necessary.
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            True if bucket exists or was created successfully
        """
        try:
            client = self.get_minio_client()
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
            return True
        except S3Error as e:
            print(f"Error ensuring bucket {bucket_name}: {e}")
            return False

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        content_type: Optional[str] = None,
    ) -> bool:
        """
        Upload a file to MinIO.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name (key)
            file_path: Local file path
            content_type: Content type (optional)
            
        Returns:
            True if upload successful
        """
        try:
            self.ensure_bucket(bucket_name)
            client = self.get_minio_client()
            client.fput_object(
                bucket_name,
                object_name,
                file_path,
                content_type=content_type,
            )
            return True
        except S3Error as e:
            print(f"Error uploading file {object_name}: {e}")
            return False

    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: Optional[str] = None,
    ) -> bool:
        """
        Upload bytes to MinIO.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name (key)
            data: Bytes to upload
            content_type: Content type (optional)
            
        Returns:
            True if upload successful
        """
        try:
            self.ensure_bucket(bucket_name)
            from io import BytesIO
            
            client = self.get_minio_client()
            client.put_object(
                bucket_name,
                object_name,
                BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return True
        except S3Error as e:
            print(f"Error uploading bytes {object_name}: {e}")
            return False

    def download_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
    ) -> bool:
        """
        Download a file from MinIO.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name (key)
            file_path: Local file path to save to
            
        Returns:
            True if download successful
        """
        try:
            client = self.get_minio_client()
            client.fget_object(bucket_name, object_name, file_path)
            return True
        except S3Error as e:
            print(f"Error downloading file {object_name}: {e}")
            return False

    def object_exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Check if object exists in bucket.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name (key)
            
        Returns:
            True if object exists
        """
        try:
            client = self.get_minio_client()
            client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False

    def generate_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires_seconds: int = 3600,
    ) -> Optional[str]:
        """
        Generate presigned URL for object access.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name (key)
            expires_seconds: URL expiration time in seconds
            
        Returns:
            Presigned URL or None on error
        """
        try:
            client = self.get_boto3_client()
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": object_name},
                ExpiresIn=expires_seconds,
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def close(self) -> None:
        """Close connections."""
        self._minio_client = None
        self._boto3_client = None


# Global connection instance (singleton pattern)
_minio_connection: Optional[MinIOConnection] = None


def get_minio_connection(env_path: Optional[Path] = None) -> MinIOConnection:
    """
    Get or create a global MinIO connection instance.
    
    Args:
        env_path: Path to .env file
    
    Returns:
        MinIOConnection instance
    """
    global _minio_connection
    if _minio_connection is None:
        _minio_connection = MinIOConnection(env_path)
    return _minio_connection
