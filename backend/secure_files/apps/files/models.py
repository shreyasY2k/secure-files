import uuid
import base64
import hashlib
import jwt

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Count
from django.utils import timezone
from django.core.exceptions import ValidationError

from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')
    mime_type = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=64, null=True, blank=True)  # SHA-256 hash
    encryption_key = models.BinaryField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            if self.file:
                # Calculate file size
                self.file.seek(0, 2)  # Seek to end
                self.file_size = self.file.tell()
                self.file.seek(0)  # Reset to beginning
                
                # Calculate checksum
                sha256 = hashlib.sha256()
                for chunk in self.file.chunks():
                    sha256.update(chunk)
                self.checksum = sha256.hexdigest()

        super().save(*args, **kwargs)

    def calculate_checksum(self, file_data):
        """Calculate SHA-256 checksum of file data"""
        sha256 = hashlib.sha256()
        if isinstance(file_data, bytes):
            sha256.update(file_data)
        else:
            for chunk in file_data.chunks():
                sha256.update(chunk)
        return sha256.hexdigest()

    def generate_fernet_key(self):
        """Generate a new Fernet key and store it in raw format"""
        fernet_key = Fernet.generate_key()  # This generates a url-safe base64-encoded key
        self.encryption_key = base64.urlsafe_b64decode(fernet_key)  # Store the raw bytes
        return fernet_key

    def get_fernet_key(self):
        """Get the Fernet key in the correct format for encryption/decryption"""
        if not self.encryption_key:
            return None
        # Convert raw bytes back to url-safe base64
        return base64.urlsafe_b64encode(self.encryption_key)

    def encrypt_file_data(self, file_data):
        """Encrypt file data using Fernet"""
        try:
            fernet_key = self.generate_fernet_key()
            # Ensure we're using bytes
            if isinstance(file_data, str):
                file_data = file_data.encode('utf-8')

            # Create Fernet cipher with properly formatted key
            fernet = Fernet(fernet_key)
            
            # Encrypt the data
            encrypted_data = fernet.encrypt(file_data)
            
            # Log for debugging
            logger.info(f"First 32 bytes of encrypted data: {encrypted_data[:32]}")
            logger.info(f"Encryption key (base64): {fernet_key.decode()}")
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}", exc_info=True)
            raise

    def decrypt_file_data(self):
        """
        Get decrypted file content
        Returns bytes of decrypted content
        """
        if not self.encryption_key:
            # If file is not encrypted, return raw content
            with self.file.open('rb') as f:
                return f.read()

        # Read encrypted content
        with self.file.open('rb') as f:
            encrypted_data = f.read()

        # Decrypt content
        try:
            # Create Fernet instance with proper key formatting
            key = base64.urlsafe_b64encode(self.encryption_key)
            # Ensure key is properly padded
            if len(key) % 4:
                key += b'=' * (4 - len(key) % 4)
            
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            logger.info(f"Decrypted data: {decrypted_data[:32]}")
            logger.info(f"Decryption key: {key.decode()}")
            return decrypted_data

        except Exception as e:
            raise ValueError(f"Failed to decrypt file: {str(e)}")

    def get_encryption_key_b64(self):
        """Get base64 encoded encryption key for client"""
        if not self.encryption_key:
            return None
        try:
            # Return the key in standard base64 format (not url-safe)
            # because the client will handle the url-safe conversion
            return base64.b64encode(self.encryption_key).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding encryption key: {str(e)}", exc_info=True)
            return None

    
    def check_storage_quota(self):
        """Check if user has exceeded their storage quota"""
        user_storage = File.objects.filter(owner=self.owner).aggregate(
            total=models.Sum('file_size')
        )['total'] or 0
        
        if user_storage + self.file_size > settings.USER_STORAGE_LIMIT:
            raise ValidationError("Storage quota exceeded")

class FileAccess(models.Model):
    """Tracks individual file access events"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='accesses')
    accessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True,  # Allow anonymous access for shared links
        blank=True,
        on_delete=models.SET_NULL
    )
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('view', 'View'),
            ('download', 'Download'),
        ]
    )
    share_link = models.ForeignKey(
        'ShareLink',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['file', 'accessed_at']),
            models.Index(fields=['accessed_by', 'accessed_at']),
        ]

class FileShare(models.Model):
    """Tracks user-to-user file sharing"""
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('download', 'Download'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shares')
    keycloak_id = models.CharField(max_length=255, default='')
    shared_with_email = models.EmailField(default='')
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    shared_with_name = models.CharField(max_length=255, default='')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ['file', 'keycloak_id']  # Prevent duplicate shares
        ordering = ['-created_at']

class ShareLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey('File', on_delete=models.CASCADE, related_name='share_links')
    token = models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_share_links'
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)
    max_access_count = models.IntegerField(null=True, blank=True)
    is_password_protected = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=128, blank=True)

    def save(self, *args, **kwargs):
        # Generate unique token if not set
        if not self.token:
            self.token = str(uuid.uuid4())
            
        # Check quota for new links
        if not self.id:
            self.check_link_quota()
            
        super().save(*args, **kwargs)
        FileStatistics.update_file_stats(self.file)

    def set_password(self, password):
        """Set password hash for password-protected link"""
        if password:
            self.is_password_protected = True
            self.password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        else:
            self.is_password_protected = False
            self.password_hash = ''

    def check_password(self, password):
        """Check if password is correct"""
        if not self.is_password_protected:
            return True
        if not password:
            return False
        return self.password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()

    def generate_access_token(self):
        """Generate a temporary access token after password verification"""
        if not self.is_valid():
            raise ValidationError("Share link is no longer valid")
        
        # Generate token
        access_token = hashlib.sha256(
            f"{self.token}{timezone.now().timestamp()}".encode('utf-8')
        ).hexdigest()
        
        access_token = jwt.encode(
            {'token': access_token},
            settings.SECRET_KEY,
            algorithm='RS256'
        )
        logging.info(f"Generated access token: {access_token}")
        # Store in cache for 1 hour
        cache_key = f"share_link_access_{self.token}"
        cache.set(cache_key, access_token, timeout=3600)  # 1 hour
        
        return access_token

    def verify_access_token(self, token):
        """Verify an access token is valid"""
        if not self.is_valid():
            return False
            
        cache_key = f"share_link_access_{self.token}"
        stored_token = cache.get(cache_key)
        
        return stored_token and stored_token == token

    def register_access(self, access_type='view', user=None, ip_address=None):
        """Register an access to the shared file"""
        now = timezone.now()
        self.last_accessed = now
        self.access_count = F('access_count') + 1
        self.save(update_fields=['last_accessed', 'access_count'])
        
        # Create access record
        FileAccess.objects.create(
            file=self.file,
            accessed_by=user,
            ip_address=ip_address,
            access_type=access_type,
            share_link=self
        )

    def check_link_quota(self):
        """Check if user has exceeded their share link quota"""
        active_links = ShareLink.objects.filter(
            created_by=self.created_by,
            expires_at__gt=timezone.now()
        ).count()
        
        if active_links >= settings.MAX_SHARE_LINKS:
            raise ValidationError("Share link quota exceeded")

    def is_valid(self):
        """Check if share link is still valid"""
        now = timezone.now()
        if now > self.expires_at:
            return False
        if self.max_access_count and self.access_count >= self.max_access_count:
            return False
        return True

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['created_by', 'created_at']),
        ]

class FileStatistics(models.Model):
    """Tracks file statistics"""
    id = models.BigAutoField(primary_key=True)
    file = models.OneToOneField('File', on_delete=models.CASCADE, related_name='statistics')
    total_views = models.IntegerField(default=0)
    total_downloads = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    share_count = models.IntegerField(default=0)
    active_share_links = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "File statistics"
        ordering = ['-updated_at']

    @classmethod
    def update_file_stats(cls, file):
        """Update file statistics"""

        # Get unique visitors
        unique_visitors = FileAccess.objects.filter(file=file).values('accessed_by').distinct().count()

        # Get access counts
        access_counts = FileAccess.objects.filter(file=file).aggregate(
            views=Count('id', filter=models.Q(access_type='view')),
            downloads=Count('id', filter=models.Q(access_type='download'))
        )

        # Get active share links count
        active_share_links = ShareLink.objects.filter(
            file=file,
            expires_at__gt=timezone.now()
        ).count()

        # Update statistics
        cls.objects.update_or_create(
            file=file,
            defaults={
                'unique_visitors': unique_visitors,
                'total_views': access_counts['views'],
                'total_downloads': access_counts['downloads'],
                'active_share_links': active_share_links,
                'share_count': file.shares.count() + file.share_links.count(),
                'last_accessed': timezone.now()
            }
        )