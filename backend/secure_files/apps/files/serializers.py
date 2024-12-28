import base64

from rest_framework import serializers
from django.conf import settings
from django.utils import timezone


from .models import File, FileShare, ShareLink, FileAccess, FileStatistics
from .utils import format_file_size

class FileSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    formatted_size = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()
    encryption_data = serializers.SerializerMethodField()
    shared_by = serializers.SerializerMethodField()
    shared_with = serializers.SerializerMethodField()
    share_info = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_share = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            'id', 'name', 'file_url', 'uploaded_at', 'owner_name',
            'file_size', 'formatted_size', 'mime_type', 'share_count',
            'encryption_data', 'shared_by', 'shared_with',
            'share_info', 'can_edit', 'can_share'
        ]
        read_only_fields = [
            'id', 'uploaded_at', 'owner_name', 'file_size',
            'formatted_size', 'mime_type', 'share_count',
            'encryption_data', 'shared_by', 'shared_with',
            'share_info', 'can_edit', 'can_share'
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(f'/api/files/{obj.id}/content/')
        return None
    
    def get_shared_with(self, obj):
        """Get list of users the file is shared with"""
        shares = FileShare.objects.filter(file=obj)
        return [
            {
                'user_id': share.keycloak_id,
                'username': share.shared_with_name,
                'email': share.shared_with_email,
                'permission': share.permission
            }
            for share in shares
        ]

    def get_shared_by(self, obj):
        """Get username of who shared the file"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Get Keycloak ID from user's token
            token = getattr(request.user, 'token', {})
            keycloak_id = token.get('sub')
            
            if keycloak_id:
                share = FileShare.objects.filter(
                    file=obj,
                    keycloak_id=keycloak_id
                ).first()
                if share:
                    return obj.owner.username
        return None

    def get_share_info(self, obj):
        """Get sharing information for the file"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Check if user is owner
            if obj.owner == request.user:
                return {
                    'is_owner': True,
                    'can_share': True,
                    'permission': 'owner'
                }
            
            # Get Keycloak ID from user's token
            token = getattr(request.user, 'token', {})
            keycloak_id = token.get('sub')
            
            if keycloak_id:
                share = FileShare.objects.filter(
                    file=obj,
                    keycloak_id=keycloak_id
                ).first()
                
                if share:
                    return {
                        'is_owner': False,
                        'can_share': share.permission == 'edit',
                        'permission': share.permission
                    }
        
        return None

    def get_can_edit(self, obj):
        """Check if user can edit the file"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Check if user is owner
            if obj.owner == request.user:
                return True
            
            # Get Keycloak ID from user's token
            token = getattr(request.user, 'token', {})
            keycloak_id = token.get('sub')
            
            if keycloak_id:
                return FileShare.objects.filter(
                    file=obj,
                    keycloak_id=keycloak_id,
                    permission='edit'
                ).exists()
        return False

    def get_can_share(self, obj):
        """Check if user can share the file"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.owner == request.user
        return False

    def get_formatted_size(self, obj):
        return format_file_size(obj.file_size)

    def get_share_count(self, obj):
        return obj.shares.count() + obj.share_links.count()

    def get_encryption_data(self, obj):
        """Return encrypted data in base64 format"""
        if obj.encryption_key:
            return {
                'key': base64.b64encode(obj.encryption_key).decode('utf-8'),
            }
        return None

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    encryption_key = serializers.CharField(required=True, allow_null=False)

    def validate(self, attrs):
        file = attrs.get('file')
        if file:
            if file.size > settings.MAX_UPLOAD_SIZE:
                raise serializers.ValidationError(
                    f"File size ({file.size} bytes) exceeds maximum allowed ({settings.MAX_UPLOAD_SIZE} bytes)"
                )
        return attrs

class FileShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileShare
        fields = [
            'id', 'file', 'keycloak_id', 'shared_with_email',
            'shared_with_name', 'permission', 'created_at',
            'last_accessed', 'access_count'
        ]
        read_only_fields = [
            'id', 'created_at', 'last_accessed', 'access_count'
        ]

    def to_representation(self, instance):
        """Enhance the response with additional data"""
        representation = super().to_representation(instance)
        representation['file'] = {
            'id': instance.file.id,
            'name': instance.file.name,
            'formatted_size': format_file_size(instance.file.file_size),
            'mime_type': instance.file.mime_type
        }
        return representation

class ShareLinkSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    file_name = serializers.CharField(source='file.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    expires_in = serializers.SerializerMethodField()
    file_size = serializers.IntegerField(source='file.file_size', read_only=True)
    formatted_file_size = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = ShareLink
        fields = [
            'id', 'token', 'file_name', 'created_by_name',
            'expires_at', 'created_at', 'last_accessed',
            'access_count', 'url', 'expires_in',
            'is_password_protected', 'max_access_count',
            'file_size', 'formatted_file_size', 'password'
        ]
        read_only_fields = [
            'id', 'token', 'created_at', 'last_accessed',
            'access_count', 'url', 'is_password_protected',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = super().create(validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance
    
    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return f"{request.scheme}://{request.get_host()}/share/{obj.token}"
        return None

    def get_formatted_file_size(self, obj):
        return format_file_size(obj.file.file_size)

    def get_expires_in(self, obj):
        """Returns time until expiration in human-readable format"""

        now = timezone.now()
        if obj.expires_at < now:
            return "Expired"

        diff = obj.expires_at - now
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60

        if days > 0:
            return f"{days} days"
        elif hours > 0:
            return f"{hours} hours"
        else:
            return f"{minutes} minutes"

class FileAccessSerializer(serializers.ModelSerializer):
    accessed_by_name = serializers.CharField(
        source='accessed_by.username',
        read_only=True,
        default='Anonymous'
    )
    file_name = serializers.CharField(source='file.name', read_only=True)
    file_size = serializers.IntegerField(source='file.file_size', read_only=True)

    class Meta:
        model = FileAccess
        fields = [
            'id', 'file_name', 'file_size', 'accessed_by_name', 
            'accessed_at', 'ip_address', 'access_type',
            'user_agent'
        ]
        read_only_fields = ['id', 'accessed_at']

class FileStatisticsSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(source='file.name', read_only=True)
    file_size = serializers.IntegerField(source='file.file_size', read_only=True)
    formatted_file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = FileStatistics
        fields = [
            'file_name', 'file_size', 'formatted_file_size',
            'total_views', 'total_downloads', 'unique_visitors',
            'last_accessed', 'share_count', 'active_share_links',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_formatted_file_size(self, obj):
        return format_file_size(obj.file.file_size)

class UserStorageSerializer(serializers.Serializer):
    used_storage = serializers.IntegerField()
    total_storage = serializers.IntegerField()
    used_links = serializers.IntegerField()
    max_links = serializers.IntegerField()
    formatted_used_storage = serializers.SerializerMethodField()
    formatted_total_storage = serializers.SerializerMethodField()
    storage_percentage = serializers.SerializerMethodField()
    active_shares = serializers.IntegerField()
    total_files = serializers.IntegerField()

    def get_formatted_used_storage(self, obj):
        return format_file_size(obj['used_storage'])

    def get_formatted_total_storage(self, obj):
        return format_file_size(obj['total_storage'])

    def get_storage_percentage(self, obj):
        if obj['total_storage'] == 0:
            return 0
        return (obj['used_storage'] / obj['total_storage']) * 100