import logging
import requests

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.conf import settings
from django.db.models import Avg
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.db.models.functions import TruncDate
from django.db import transaction

from secure_files.apps.files.models import File, FileShare, ShareLink, FileAccess
from .serializers import (
    UserAdminSerializer,
    UserStatsSerializer,
    SystemStatsSerializer,
    CreateUserSerializer
)
from .permissions import HasKeycloakRole
from .keycloak_admin import KeycloakAdmin, KeycloakError
from datetime import timedelta

logger = logging.getLogger(__name__)

class AdminViewSet(viewsets.ViewSet):
    basename = 'admin'
    permission_classes = [HasKeycloakRole(['admin'])]

    @action(detail=False, methods=['get'], url_path='check-admin-access')
    def check_admin_access(self, request):
        """Check if the current user has admin access"""
        # Get token from request
        token = getattr(request.user, 'token', {})
        realm_access = token.get('realm_access', {})
        roles = realm_access.get('roles', [])
        print(f"User roles: {roles}")  # Debug print
        return Response({
            'is_admin': 'admin' in roles,
            'roles': roles
        })
    
    @action(detail=False, methods=['post'], url_path='create-user')
    def create_user(self, request):
        """Create a new user in both Keycloak and Django"""
        try:
            serializer = CreateUserSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            keycloak_admin = KeycloakAdmin()

            with transaction.atomic():
                # Create user in Keycloak
                keycloak_user_id = keycloak_admin.create_user(
                    user_data=validated_data,
                    role=validated_data['role']
                )

                # Create user in Django
                user = User.objects.create_user(
                    username=validated_data['username'],
                    email=validated_data['email'],
                    password=validated_data['password']
                )

            return Response({
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': validated_data['role']
                }
            }, status=status.HTTP_201_CREATED)

        except KeycloakError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            return Response(
                {'error': 'Failed to create user'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['delete'], url_path='delete-user')
    def delete_user(self, request, pk=None):
        """Delete user from both Keycloak and Django"""
        try:
            user = User.objects.get(pk=pk)
            keycloak_admin = KeycloakAdmin()

            with transaction.atomic():
                # Get Keycloak user ID
                keycloak_user_id = keycloak_admin.get_user_id_by_username(user.username)
                
                if keycloak_user_id:
                    # Delete from Keycloak
                    keycloak_admin.delete_user(keycloak_user_id)

                # Delete from Django
                user.delete()

            return Response({
                'message': 'User deleted successfully'
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except KeycloakError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"User deletion error: {str(e)}")
            return Response(
                {'error': 'Failed to delete user'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='storage-stats')
    def storage_stats(self, request):
        """Get storage statistics for the current user"""
        user = request.user
        token = getattr(user, 'token', {})
        roles = token.get('realm_access', {}).get('roles', [])

        if 'admin' in roles:
            # Admins see system-wide stats
            total_used_storage = File.objects.aggregate(total=Sum('file_size'))['total'] or 0
            used_links = ShareLink.objects.count()
            storage_limit = settings.SYSTEM_STORAGE_LIMIT

            # Get per-user stats for system overview
            user_stats = User.objects.annotate(
                user_storage=Coalesce(Sum('file__file_size'), 0)
            ).aggregate(
                total_users=Count('id'),
                active_users=Count('id', filter=Q(is_active=True)),
                allocated_storage=Count('id') * settings.USER_STORAGE_LIMIT
            )

            return Response({
                'used_storage': total_used_storage,
                'total_storage': storage_limit,
                'used_links': used_links,
                'max_links': settings.MAX_SHARE_LINKS,
                'storage_usage': {
                    'used': total_used_storage,
                    'total': storage_limit,
                    'used_percentage': (total_used_storage / storage_limit) * 100 if storage_limit else 0,
                    'allocated_storage': user_stats['allocated_storage'],  # Total storage allocated to users
                    'total_users': user_stats['total_users'],
                    'active_users': user_stats['active_users']
                }
            })
        else:
            # Regular users see their own stats
            used_storage = File.objects.filter(owner=user).aggregate(
                total=Sum('file_size'))['total'] or 0
            used_links = ShareLink.objects.filter(file__owner=user).count()

            return Response({
                'used_storage': used_storage,
                'total_storage': settings.USER_STORAGE_LIMIT,
                'used_links': used_links,
                'max_links': settings.MAX_SHARE_LINKS,
                'storage_percentage': (used_storage / settings.USER_STORAGE_LIMIT) * 100
            })

    def get_system_overview(self):
        """Get system-wide overview statistics"""
        total_users = User.objects.count()
        total_files = File.objects.count()
        total_storage = File.objects.aggregate(total=Sum('file_size'))['total'] or 0
        total_shares = ShareLink.objects.count()

        active_users = User.objects.filter(
            last_login__gt=timezone.now() - timedelta(days=30)
        ).count()

        active_shares = ShareLink.objects.filter(
            expires_at__gt=timezone.now()
        ).count()

        # Calculate storage usage percentage
        storage_limit = 1024 * 1024 * 1024 * 1024  # 1TB example limit
        storage_usage_percent = (total_storage / storage_limit) * 100 if storage_limit > 0 else 0

        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_files': total_files,
            'total_storage': total_storage,
            'formatted_storage': self.format_size(total_storage),
            'storage_usage_percent': round(storage_usage_percent, 2),
            'total_shares': total_shares,
            'active_shares': active_shares
        }

    def get_activity_trends(self):
        """Get activity trends for the last 30 days"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # File uploads over time
        file_uploads = File.objects.filter(
            uploaded_at__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('uploaded_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Share creation trends
        share_creation = ShareLink.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # User registration trends
        user_registrations = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('date_joined')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # File access trends
        file_access = FileAccess.objects.filter(
            accessed_at__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('accessed_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        return {
            'file_uploads': list(file_uploads),
            'share_creation': list(share_creation),
            'user_registrations': list(user_registrations),
            'file_access': list(file_access)
        }

    def get_storage_analytics(self):
        """Get detailed storage analytics"""
        # Storage distribution by file type
        storage_by_type = File.objects.values('mime_type').annotate(
            total_size=Sum('file_size'),
            file_count=Count('id')
        ).order_by('-total_size')

        # Top storage users
        top_users = User.objects.annotate(
            storage_used=Sum('file__file_size'),
            file_count=Count('file')
        ).exclude(
            storage_used=None
        ).order_by('-storage_used')[:10]

        # Storage growth over time (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        storage_growth = File.objects.filter(
            uploaded_at__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('uploaded_at')
        ).values('date').annotate(
            total_size=Sum('file_size')
        ).order_by('date')

        return {
            'storage_by_type': [
                {
                    'mime_type': item['mime_type'],
                    'total_size': item['total_size'],
                    'formatted_size': self.format_size(item['total_size']),
                    'file_count': item['file_count']
                }
                for item in storage_by_type
            ],
            'top_users': [
                {
                    'username': user.username,
                    'storage_used': user.storage_used,
                    'formatted_storage': self.format_size(user.storage_used),
                    'file_count': user.file_count
                }
                for user in top_users
            ],
            'storage_growth': list(storage_growth)
        }

    def get_user_analytics(self):
        """Get detailed user analytics"""
        # Active vs Inactive users
        total_users = User.objects.count()
        active_users = User.objects.filter(
            last_login__gt=timezone.now() - timedelta(days=30)
        ).count()

        # User engagement metrics
        user_engagement = User.objects.annotate(
            files_uploaded=Count('file'),
            shares_created=Count('created_share_links'),
            received_shares=Count('fileshare')
        ).aggregate(
            avg_files=Avg('files_uploaded'),
            avg_shares=Avg('shares_created'),
            avg_received=Avg('received_shares')
        )

        # Most active users
        most_active = User.objects.annotate(
            activity_score=Count('file') + Count('created_share_links') + Count('fileshare')
        ).order_by('-activity_score')[:10]

        return {
            'user_distribution': {
                'total': total_users,
                'active': active_users,
                'inactive': total_users - active_users
            },
            'engagement_metrics': user_engagement,
            'most_active_users': [
                {
                    'username': user.username,
                    'activity_score': user.activity_score,
                    'last_login': user.last_login
                }
                for user in most_active
            ]
        }

    @staticmethod
    def format_size(size):
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    @action(detail=False, methods=['get'], url_path='system-stats')
    def system_stats(self, request):
        """Get system-wide statistics"""
        try:
            keycloak_admin = KeycloakAdmin()
            keycloak_users = keycloak_admin.get_all_users()
            # Count total and active users
            total_users = len(keycloak_users)
            active_users = sum(1 for user in keycloak_users if user.get('enabled', False) and user.get('totp', False))

            # Get file and storage statistics
            total_files = File.objects.count()
            total_storage = File.objects.aggregate(total=Sum('file_size'))['total'] or 0
            total_shares = ShareLink.objects.count()
            active_shares = ShareLink.objects.filter(
                expires_at__gt=timezone.now()
            ).count()

            data = {
                'total_users': total_users,
                'active_users': active_users,
                'total_files': total_files,
                'total_storage': total_storage,
                'total_shares': total_shares,
                'active_shares': active_shares,
                'storage_by_user': self.get_storage_by_user(),
                'files_by_type': self.get_files_by_type(),
                'user_activity': self.get_user_activity(keycloak_users),
                'storage_usage': {
                    'used': total_storage,
                    'total': settings.SYSTEM_STORAGE_LIMIT,
                    'used_percentage': (total_storage / settings.SYSTEM_STORAGE_LIMIT) * 100 if settings.SYSTEM_STORAGE_LIMIT else 0,
                    'allocated_storage': total_users * settings.USER_STORAGE_LIMIT
                }
            }

            serializer = SystemStatsSerializer(data)
            return Response(serializer.data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Keycloak: {str(e)}")
            return Response(
                {'error': 'Failed to fetch user data from Keycloak'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error getting system stats: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='user-management')
    def user_management(self, request):
        """Get user list with their stats"""
        try:
            keycloak_admin = KeycloakAdmin()
            keycloak_users = keycloak_admin.get_all_users()
    
            # Process user data
            user_data = []
            for user in keycloak_users:
                # Get user roles
                user_roles_response = keycloak_admin.get_user_roles(user['id'])

                roles = [role['name'] for role in user_roles_response.json()]
                logger.info(f"User roles: user={user}, roles={roles}")
                # Convert timestamps
                last_login = user.get('lastLogin')
                if last_login:
                    last_login = timezone.datetime.fromisoformat(last_login.replace('Z', '+00:00'))
    
                created_timestamp = user.get('createdTimestamp')
                if created_timestamp:
                    created_timestamp = timezone.datetime.fromtimestamp(created_timestamp / 1000, tz=timezone.utc)
    
                user_data.append({
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'is_active': user.get('enabled', False) and user.get('totp', False),
                    'last_login': last_login,
                    'createdTimestamp': created_timestamp,
                    'roles': roles
                })
    
            serializer = UserStatsSerializer(user_data, many=True, context={'request': request})
            return Response(serializer.data)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Keycloak: {str(e)}")
            return Response(
                {'error': 'Failed to fetch user data from Keycloak'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error getting user management data: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_user_status(self, request, pk=None):
        """Toggle user active status"""
        try:
            keycloak_admin = KeycloakAdmin()
            user = keycloak_admin.get_user_by_id(pk)
            logger.info(f"User data: {user}")
            current_status = user.get('enabled', False)
            # user.enabled = not user.enabled
            user['enabled'] = not current_status

            # Also update Keycloak user status
            keycloak_admin.update_user_status(user['id'], user['enabled'])
            
            return Response({
                'id': user['id'],
                'username': user['username'],
                'is_active': user['enabled'],
                'status': 'success'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error toggling user status: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_storage_by_user(self):
        """Get storage usage by user"""
        return User.objects.annotate(
            storage_used=Sum('file__file_size')
        ).values(
            'username',
            'email',
            'storage_used'
        ).exclude(
            storage_used=None
        ).order_by('-storage_used')[:10]

    def get_files_by_type(self):
        """Get file count by type"""
        return File.objects.values('mime_type').annotate(
            count=Count('id')
        ).order_by('-count')

    def get_user_activity(self, users):
        """Get user activity over last 30 days from Keycloak"""
        try:
            # Process user activity data
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            activity_data = {}

            for user in users:
                # Get last login timestamp from Keycloak user data
                last_login = None
                if user.get('enabled', False):
                    # Try to get timestamp from different possible Keycloak fields
                    timestamps = []
                    if 'lastLogin' in user:
                        timestamps.append(user['lastLogin'])
                    if 'lastSession' in user:
                        timestamps.append(user['lastSession'])

                    # Get the most recent timestamp
                    if timestamps:
                        last_login = max(timestamps)

                if last_login:
                    # Convert timestamp to date
                    login_date = timezone.datetime.fromisoformat(last_login.replace('Z', '+00:00')).date()

                    # Only count if within last 30 days
                    if login_date >= thirty_days_ago.date():
                        activity_data[login_date] = activity_data.get(login_date, 0) + 1

            # Convert to list and sort by date
            activity_list = [
                {
                    'date': date.isoformat(),
                    'count': count
                }
                for date, count in sorted(activity_data.items())
            ]

            return activity_list

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user activity from Keycloak: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error processing user activity data: {str(e)}")
            return []

    def get_user_files_by_type(self, user):
        """Get file types for a specific user"""
        return File.objects.filter(
            owner__email=user.email
        ).values('mime_type').annotate(
            count=Count('id')
        ).order_by('-count')

    def get_user_recent_activity(self, user):
        """Get recent activity for a specific user"""
        try:
            return FileAccess.objects.filter(
                file__owner__email=user.email
            ).select_related('file').order_by('-accessed_at')[:10]
        except Exception:
            return []

    @action(detail=True, methods=['get'], url_path='details')
    def user_details(self, request, pk=None):
        """Get detailed user stats"""
        try:
            user = User.objects.get(pk=pk)
            used_storage = File.objects.filter(owner__email=user.email).aggregate(
                total=Sum('file_size'))['total'] or 0

            data = {
                'user': UserAdminSerializer(user).data,
                'storage': {
                    'used': used_storage,
                    'formatted_used': self.format_size(used_storage),
                    'files_count': File.objects.filter(owner__email=user.email).count(),
                    'files_by_type': self.get_user_files_by_type(user)
                },
                'sharing': {
                    'active_shares': ShareLink.objects.filter(
                        file__owner__email=user.email,
                        expires_at__gt=timezone.now()
                    ).count(),
                    'total_shares': ShareLink.objects.filter(
                        file__owner__email=user.email
                    ).count(),
                    'shared_with_others': FileShare.objects.filter(
                        file__owner__email=user.email
                    ).count()
                },
                'activity': {
                    'last_login': user.last_login,
                    'date_joined': user.date_joined,
                    'recent_activity': self.get_user_recent_activity(user)
                }
            }
            return Response(data)

        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting user details: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def format_size(size):
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"