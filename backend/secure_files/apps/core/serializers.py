from rest_framework import serializers

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count

from secure_files.apps.files.models import File, FileShare, ShareLink

class UserStatsSerializer(serializers.Serializer):
    id = serializers.CharField()
    username = serializers.CharField()
    email = serializers.EmailField()
    is_active = serializers.BooleanField()
    last_login = serializers.DateTimeField(allow_null=True)
    date_joined = serializers.DateTimeField(source='createdTimestamp')
    storage_used = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()
    active_shares = serializers.SerializerMethodField()
    total_shares = serializers.SerializerMethodField()
    formatted_storage = serializers.SerializerMethodField()
    files_by_type = serializers.SerializerMethodField()
    activity_stats = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    def get_storage_used(self, obj):
        return File.objects.filter(owner__email=obj['email']).aggregate(
            total=Sum('file_size'))['total'] or 0

    def get_file_count(self, obj):
        return File.objects.filter(owner__email=obj['email']).count()

    def get_active_shares(self, obj):
        return ShareLink.objects.filter(
            file__owner__email=obj['email'],
            expires_at__gt=timezone.now()
        ).count()

    def get_total_shares(self, obj):
        return ShareLink.objects.filter(file__owner__email=obj['email']).count()

    def get_formatted_storage(self, obj):
        size = self.get_storage_used(obj)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def get_files_by_type(self, obj):
        return File.objects.filter(owner__email=obj['email']).values('mime_type').annotate(
            count=Count('id')
        ).order_by('-count')

    def get_activity_stats(self, obj):
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        return {
            'file_uploads': File.objects.filter(
                owner__email=obj['email'],
                uploaded_at__gte=thirty_days_ago
            ).count(),
            'shares_created': ShareLink.objects.filter(
                file__owner__email=obj['email'],
                created_at__gte=thirty_days_ago
            ).count(),
            'received_shares': FileShare.objects.filter(
                shared_with_email=obj['email'],
                created_at__gte=thirty_days_ago
            ).count()
        }

    def get_roles(self, obj):
        return obj.get('roles', [])

class SystemStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_files = serializers.IntegerField()
    total_storage = serializers.IntegerField()
    total_shares = serializers.IntegerField()
    active_shares = serializers.IntegerField()
    storage_by_user = serializers.ListField()
    files_by_type = serializers.ListField()
    user_activity = serializers.ListField()
    storage_usage = serializers.SerializerMethodField()
    formatted_total_storage = serializers.SerializerMethodField()
    daily_stats = serializers.SerializerMethodField()

    def get_storage_usage(self, obj):
        """Get storage usage statistics including both used and allocated storage"""
        system_storage_limit = getattr(settings, 'SYSTEM_STORAGE_LIMIT', 1024 * 1024 * 1024 * 1024)  # 1TB default
        total_allocated = obj['total_users'] * settings.USER_STORAGE_LIMIT

        return {
            'used': obj['total_storage'],
            'total': system_storage_limit,
            'used_percentage': (obj['total_storage'] / system_storage_limit * 100) if system_storage_limit else 0,
            'allocated_storage': total_allocated,
            'allocated_percentage': (total_allocated / system_storage_limit * 100) if system_storage_limit else 0,
            'formatted_used': self._format_size(obj['total_storage']),
            'formatted_total': self._format_size(system_storage_limit),
            'formatted_allocated': self._format_size(total_allocated)
        }

    def get_formatted_total_storage(self, obj):
        return self._format_size(obj['total_storage'])

    def _format_size(self, size):
        if size == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        i = 0
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.2f} {units[i]}"

    def get_daily_stats(self, obj):
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        daily_stats = []
        
        for day in range(30):
            date = timezone.now() - timezone.timedelta(days=day)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timezone.timedelta(days=1)
            
            daily_stats.append({
                'date': date_start.date().isoformat(),
                'new_users': User.objects.filter(
                    date_joined__range=(date_start, date_end)
                ).count(),
                'file_uploads': File.objects.filter(
                    uploaded_at__range=(date_start, date_end)
                ).count(),
                'shares_created': ShareLink.objects.filter(
                    created_at__range=(date_start, date_end)
                ).count()
            })
        
        return daily_stats

class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'date_joined', 'last_login']

class CreateUserSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    firstName = serializers.CharField(required=False)
    lastName = serializers.CharField(required=False)
    role = serializers.ChoiceField(choices=['user', 'admin', 'guest'], default='user')