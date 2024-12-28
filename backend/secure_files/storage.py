# backend/secure_files/storage.py
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import boto3
from botocore.exceptions import ClientError
from django.core.exceptions import SuspiciousFileOperation
import logging

logger = logging.getLogger(__name__)

class SecureFileSystemStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_quota_bytes = 2 * 1024 * 1024 * 1024  # 2GB

    def _save(self, name, content):
        if not self.has_quota_available(content.size):
            raise QuotaExceededException("Storage quota exceeded")
        return super()._save(name, content)

    def has_quota_available(self, file_size):
        """Check if user has enough quota available"""
        from secure_files.apps.files.models import File
        used_storage = File.objects.filter(owner=self.request.user).aggregate(
            total=models.Sum('file_size')
        )['total'] or 0
        return (used_storage + file_size) <= self.base_quota_bytes

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME

    def _save(self, name, content):
        try:
            self.s3_client.upload_fileobj(content, self.bucket, name)
            return name
        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise

    def _open(self, name, mode='rb'):
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=name)
            return response['Body']
        except ClientError as e:
            logger.error(f"Error downloading from S3: {str(e)}")
            raise

class QuotaExceededException(Exception):
    pass

def get_storage_backend():
    """Factory function to get the appropriate storage backend"""
    storage_type = os.getenv('STORAGE_BACKEND', 'local').lower()
    
    if storage_type == 'local':
        return SecureFileSystemStorage(
            location=settings.MEDIA_ROOT,
            base_url=settings.MEDIA_URL
        )
    elif storage_type == 's3':
        return S3Storage()
    else:
        raise ValueError(f"Unknown storage backend: {storage_type}")