import os
import logging
import uuid
import base64
import magic
import mimetypes
from datetime import timedelta

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import F
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Sum
from django.db.models import Q
from django.db.models import Sum

from .models import File, FileShare, ShareLink, FileAccess, FileStatistics
from .serializers import (
    FileSerializer, FileShareSerializer, ShareLinkSerializer,
)
from ..core.keycloak_admin import KeycloakAdmin
from secure_files.apps.core.permissions import HasKeycloakRole

logger = logging.getLogger(__name__)

class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    serializer_class = FileSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get base queryset for the view"""
        user = self.request.user
        
        # Check if user exists and is authenticated
        if not user or not user.is_authenticated:
            logger.warning("Unauthenticated access attempt to file list")
            return File.objects.none()

        # Get user's token and roles
        token = getattr(user, 'token', {})
        roles = token.get('realm_access', {}).get('roles', [])
        logger.info(f"User roles: {roles}")

        # If admin, return all files
        if 'admin' in roles:
            logger.info("Admin access - returning all files")
            return File.objects.all()

        # For regular users, return their files and files shared with them
        elif 'user' in roles:
            logger.info(f"User access for {user.username}")
            return (
                File.objects.filter(
                    Q(owner=user) |  # Files owned by user
                    Q(shares__keycloak_id=token.get('sub'))  # Files shared with user
                )
                .distinct()  # Remove duplicates
                .select_related('owner')  # Optimize queries
                .prefetch_related('shares')
            )

        # Default to no files if no matching roles
        logger.warning(f"No matching roles for user {user.username}")
        return File.objects.none()


    def apply_search_filter(self, queryset):
        """Apply search filter to queryset"""
        search_query = self.request.query_params.get('search', '').strip()
        if search_query:
            return queryset.filter(
                Q(name__icontains=search_query) |
                Q(mime_type__icontains=search_query)
            )
        return queryset

    def apply_date_filter(self, queryset):
        """Apply date range filter to queryset"""
        date_range = self.request.query_params.get('date_range', 'all')
        now = timezone.now()

        if date_range == '7days':
            start_date = now - timedelta(days=7)
        elif date_range == '30days':
            start_date = now - timedelta(days=30)
        elif date_range == '90days':
            start_date = now - timedelta(days=90)
        else:  # 'all'
            return queryset

        return queryset.filter(uploaded_at__gte=start_date)

    def apply_type_filter(self, queryset):
        """Apply file type filter to queryset"""
        file_type = self.request.query_params.get('file_type', 'all')

        if file_type == 'document':
            return queryset.filter(
                Q(mime_type__icontains='pdf') |
                Q(mime_type__icontains='document') |
                Q(mime_type__icontains='text')
            )
        elif file_type == 'image':
            return queryset.filter(mime_type__istartswith='image/')
        elif file_type == 'other':
            return queryset.exclude(
                Q(mime_type__istartswith='image/') |
                Q(mime_type__icontains='pdf') |
                Q(mime_type__icontains='document') |
                Q(mime_type__icontains='text')
            )
        return queryset

    def apply_sorting(self, queryset):
        """Apply sorting to queryset"""
        sort_by = self.request.query_params.get('sort_by', 'uploaded_at')
        order = self.request.query_params.get('order', 'desc')
        
        valid_sort_fields = {
            'name': 'name',
            'size': 'file_size',
            'uploaded_at': 'uploaded_at',
            'type': 'mime_type'
        }

        # Get the actual field name or default to 'uploaded_at'
        sort_field = valid_sort_fields.get(sort_by, 'uploaded_at')
        
        # Apply ordering
        if order == 'asc':
            return queryset.order_by(sort_field)
        return queryset.order_by(f'-{sort_field}')

    def list(self, request, *args, **kwargs):
        """Enhanced list method with filtering, searching, and sorting"""
        try:
            logger.info(f"List request from user: {request.user.username}")
            
            # Get base queryset
            queryset = self.get_queryset()
            if queryset is None:
                logger.error("get_queryset returned None")
                return Response(
                    {'error': 'Failed to initialize file list'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Log initial queryset count
            initial_count = queryset.count()
            logger.info(f"Initial queryset count: {initial_count}")

            # Apply filters
            queryset = self.apply_search_filter(queryset)
            queryset = self.apply_date_filter(queryset)
            queryset = self.apply_type_filter(queryset)
            queryset = self.apply_sorting(queryset)

            # Log final queryset count
            final_count = queryset.count()
            logger.info(f"Final queryset count after filters: {final_count}")

            # Paginate results
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.exception("Error in file list")  # This logs the full traceback
            return Response(
                {
                    'error': 'Failed to retrieve files',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_permissions(self):
        logger.info(f"\n=== Getting permissions for action: {self.action} ===")
        
        if self.action == 'get_shared_file':
            permission_classes = [AllowAny]
        elif self.action == 'download_shared_file':
            permission_classes = [AllowAny]
        elif self.action == 'shared_with_me':
            # Changed from ['user'] to ['USER']
            permission_classes = [HasKeycloakRole(['user', 'admin'])]
        else:
            permission_classes = [HasKeycloakRole(['user', 'admin'])]
            
        logger.info(f"Selected permission classes: {permission_classes}")
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        file_obj = serializer.validated_data['file']
        # Set file size before saving
        file_size = file_obj.size
        serializer.save(
            owner=self.request.user,
            file_size=file_size
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Record file access
        FileAccess.objects.create(
            file=instance,
            accessed_by=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            access_type='view'
        )
        # Update statistics
        FileStatistics.update_statistics(instance.id)
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share a file with another user"""
        try:
            file = self.get_object()
            if file.owner != request.user:
                return Response(
                    {'error': 'Cannot share files owned by other users'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get the user from Keycloak
            shared_with_email = request.data.get('shared_with')
            if not shared_with_email:
                return Response(
                    {'error': 'Email address is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            keycloak_user = KeycloakAdmin().get_user_by_email(shared_with_email)
            if not keycloak_user:
                return Response(
                    {'error': f'No user found with email {shared_with_email}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            logger.info(f"Keycloak user: {keycloak_user}")
            # Check if share already exists
            existing_share = FileShare.objects.filter(
                file=file,
                keycloak_id=keycloak_user['id']
            ).first()

            if existing_share:
                logger.info(f"Updating existing share for {shared_with_email}")
                # Update existing share
                existing_share.permission = request.data.get('permission', 'view')
                existing_share.save()
                share = existing_share
            else:
                # Create new share
                logger.info(f"Creating new share for {shared_with_email}")
                share = FileShare.objects.create(
                    file=file,
                    keycloak_id=keycloak_user['id'],
                    shared_with_email=keycloak_user['email'],
                    shared_with_name=f"{keycloak_user.get('firstName', '')} {keycloak_user.get('lastName', '')}".strip() or keycloak_user['username'],
                    permission=request.data.get('permission', 'view')
                )

            serializer = FileShareSerializer(share)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error sharing file: {str(e)}")
            return Response(
                {'error': str(e) if settings.DEBUG else 'Failed to share file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='upload')
    def upload_file(self, request):
        try:
            file_obj = request.FILES.get('file')
            if not file_obj:
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check file size
            if file_obj.size > settings.MAX_UPLOAD_SIZE:
                return Response({
                    'error': f'File size exceeds limit of {settings.MAX_UPLOAD_SIZE / (1024*1024):.1f} MB'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check quota
            used_storage = File.objects.filter(owner=request.user).aggregate(
                total=Sum('file_size'))['total'] or 0
            if hasattr(settings, 'USER_STORAGE_LIMIT') and used_storage + file_obj.size > settings.USER_STORAGE_LIMIT:
                return Response(
                    {'error': 'Storage quota exceeded'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Read file content
            file_content = file_obj.read()
            file_obj.seek(0)

            original_filename = request.POST.get('original_filename') or file_obj.name
            # Get MIME type
            mime_type = request.POST.get('mime_type') or magic.from_buffer(file_content[:1024], mime=True)

            # Generate unique filename
            file_extension = file_obj.name.split('.')[-1] if '.' in file_obj.name else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}"

            # Create file instance
            file_instance = File(
                name=original_filename,
                owner=request.user,
                mime_type=mime_type,
                file_size=file_obj.size
            )

            # Calculate checksum before encryption
            file_instance.checksum = file_instance.calculate_checksum(file_content)

            # Handle encryption
            file_content = file_instance.encrypt_file_data(file_content)

            # Save file
            file_path = default_storage.save(
                f'uploads/{unique_filename}',
                ContentFile(file_content)
            )
            file_instance.file = file_path
            file_instance.save()

            serializer = self.get_serializer(file_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        """Get decrypted file content"""
        try:
            file_instance = self.get_object()
            decrypted_content = file_instance.decrypt_file_data()

            response = HttpResponse(
                decrypted_content,
                content_type=file_instance.mime_type or 'application/octet-stream'
            )

            if request.GET.get('download'):
                response['Content-Disposition'] = f'attachment; filename="{file_instance.name}"'

            # Record access
            FileAccess.objects.create(
                file=file_instance,
                accessed_by=request.user if request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                access_type='download' if request.GET.get('download') else 'view'
            )

            return response

        except Exception as e:
            logger.error(f"Content access error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['get'], url_path='storage-stats')
    def storage_stats(self, request):
        """Get storage statistics for the current user"""
        user = request.user
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


    @action(detail=True, methods=['post'], url_path='share-link')
    def create_share_link(self, request, pk=None):
        """Create a share link for a file"""
        if 'guest' in request.user.token.get('realm_access', {}).get('roles', []):
            return Response(
                {'error': 'Guests cannot create share links'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            file = self.get_object()
            
            # Check share link quota
            used_links = ShareLink.objects.filter(file__owner=request.user).count()
            if used_links >= settings.MAX_SHARE_LINKS:
                return Response({
                    'error': 'Share link quota exceeded'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get expiration time from request or default to 24 hours
            expires_in_hours = int(request.data.get('expires_in_hours', 24))
            expires_at = timezone.now() + timezone.timedelta(hours=expires_in_hours)

            # Create share link
            share_link = ShareLink.objects.create(
                file=file,
                created_by=request.user,
                token=str(uuid.uuid4()),
                expires_at=expires_at,
                max_access_count=request.data.get('max_access_count'),
                is_password_protected=bool(request.data.get('password'))
            )

            # Set password if provided
            if request.data.get('password'):
                share_link.set_password(request.data['password'])
                share_link.save()

            serializer = ShareLinkSerializer(share_link, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='shared-with-me')
    def shared_with_me(self, request):
        """
        Get files shared with the current user based on Keycloak ID
        """
        try:
            # Get Keycloak ID from user's token
            token = getattr(request.user, 'token', {})
            keycloak_id = token.get('sub')
            
            if not keycloak_id:
                logger.error(f"No Keycloak ID found for user {request.user.username}")
                return Response(
                    {'error': 'User identification not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
            logger.info(f"Finding files shared with Keycloak ID: {keycloak_id}")
    
            # Get files shared with user's Keycloak ID
            queryset = File.objects.filter(
                shares__keycloak_id=keycloak_id
            ).distinct()
    
            # Log initial count
            logger.info(f"Found {queryset.count()} shared files before filtering")
    
            # Apply filters
            queryset = self.apply_search_filter(queryset)
            queryset = self.apply_date_filter(queryset)
            queryset = self.apply_type_filter(queryset)
            queryset = self.apply_sorting(queryset)
    
            # Log final count
            logger.info(f"Returning {queryset.count()} shared files after filtering")
    
            # Handle pagination if configured
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
    
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
    
        except Exception as e:
            logger.exception("Error retrieving shared files")  # This logs the full traceback
            return Response(
                {
                    'error': 'Failed to retrieve shared files',
                    'detail': str(e) if settings.DEBUG else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='recent')
    def recent_files(self, request):
        """
        Get recent files (last 7 days)
        """
        try:
            seven_days_ago = timezone.now() - timedelta(days=7)
            queryset = self.get_queryset().filter(uploaded_at__gte=seven_days_ago)
            queryset = self.apply_sorting(queryset)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error retrieving recent files: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve recent files'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """Override create to set owner"""
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        """Override destroy to check ownership"""
        if instance.owner != self.request.user and 'admin' not in self.request.user.token.get('realm_access', {}).get('roles', []):
            raise PermissionError("Cannot delete files owned by other users")
        instance.delete()

    # @action(detail=True, methods=['post'])
    # def share(self, request, pk=None):
    #     """Share a file with another user"""
    #     try:
    #         file = self.get_object()
    #         if file.owner != request.user and 'admin' not in request.user.token.get('realm_access', {}).get('roles', []):
    #             return Response(
    #                 {'error': 'Cannot share files owned by other users'},
    #                 status=status.HTTP_403_FORBIDDEN
    #             )
    
    #         shared_with = request.data.get('shared_with')  # Match the frontend parameter name
    #         permission = request.data.get('permission', 'view')

    #         if not shared_with:
    #             return Response(
    #                 {'error': 'shared_with parameter is required'},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    
    #         # Check if share already exists
    #         existing_share = FileShare.objects.filter(
    #             file=file,
    #             shared_with=shared_with
    #         ).first()
    
    #         if existing_share:
    #             # Update existing share
    #             existing_share.permission = permission
    #             existing_share.save()
    #             share = existing_share
    #         else:
    #             # Create new share
    #             logger.info(f"Creating new share for {shared_with}")
    #             share = FileShare.objects.create(
    #                 file=file,
    #                 shared_with=shared_with,
    #                 permission=permission
    #             )
    
    #         return Response({
    #             'id': share.id,
    #             'shared_with': share.shared_with,
    #             'permission': share.permission,
    #             'created_at': share.created_at
    #         })
    
    #     except FileShare.DoesNotExist:
    #         return Response(
    #             {'error': 'Share not found'},
    #             status=status.HTTP_404_NOT_FOUND
    #         )
    #     except Exception as e:
    #         logger.error(f"Error sharing file: {str(e)}")
    #         return Response(
    #             {'error': str(e) if settings.DEBUG else 'Failed to share file'},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
            # )


    @action(detail=True, methods=['get'], url_path='statistics')
    def get_statistics(self, request, pk=None):
        """Get statistics for a file"""
        file = self.get_object()
        stats, _ = FileStatistics.objects.get_or_create(file=file)
        return Response({
            'total_views': stats.total_views,
            'total_downloads': stats.total_downloads,
            'unique_visitors': stats.unique_visitors,
            'share_count': stats.share_count,
            'active_share_links': stats.active_share_links,
            'last_accessed': stats.last_accessed
        })

    def format_size(self, size):
        """Format file size to human readable format"""
        try:
            # Ensure size is a number
            size = float(size)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except (TypeError, ValueError):
            return "0 B"

    @action(detail=False, methods=['get'], url_path='shared/(?P<token>[^/.]+)', permission_classes=[AllowAny])
    def get_shared_file(self, request, token=None):
        """Get shared file information"""
        try:
            # Get the share link
            share_link = ShareLink.objects.select_related('file').get(
                token=token,
                expires_at__gt=timezone.now()
            )

            # Check access count if set
            if share_link.max_access_count and share_link.access_count >= share_link.max_access_count:
                return Response(
                    {'error': 'Maximum access count exceeded'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Increment access count
            # share_link.access_count += 1
            share_link.last_accessed = timezone.now()
            share_link.save()

            # Record access
            FileAccess.objects.create(
                file=share_link.file,
                accessed_by=request.user if request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                access_type='view',
                share_link=share_link
            )

            # Return file info
            return Response({
                'id': str(share_link.file.id),
                'name': share_link.file.name,
                'size': share_link.file.file_size,
                'formatted_size': self.format_size(share_link.file.file_size),
                'uploaded_at': share_link.file.uploaded_at,
                'is_password_protected': share_link.is_password_protected,
                'max_access_count': share_link.max_access_count,
                'access_count': share_link.access_count,
                'expires_at': share_link.expires_at
            })

        except ShareLink.DoesNotExist:
            return Response(
                {'error': 'Share link not found or has expired'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='download/(?P<token>[^/.]+)')
    def download_shared_file(self, request, token=None):
        try:
            share_link = ShareLink.objects.select_related('file').get(
                token=token,
                expires_at__gt=timezone.now()
            )

            if share_link.max_access_count and share_link.access_count >= share_link.max_access_count:
                return Response(
                    {'error': 'Maximum access count exceeded'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Verify access token for password-protected files
            if share_link.is_password_protected:
                auth_header = request.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    return Response(
                        {'error': 'Access token required'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                access_token = auth_header.split(' ', 1)[1].strip()
                if not share_link.verify_access_token(access_token):
                    return Response(
                        {'error': 'Invalid or expired access token'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

            # Read file content (already encrypted)
            # with share_link.file.file.open('rb') as f:
            #     file_content = f.read()

            file_content = share_link.file.decrypt_file_data()
            # Create response with encrypted content
            response = HttpResponse(
                file_content,
                content_type='application/octet-stream'
            )

            response['Content-Disposition'] = f'attachment; filename="{share_link.file.name}"'
            
            if share_link.file.encryption_key:
                logger.info("File is encrypted")
                encryption_key = share_link.file.get_encryption_key_b64()
                logger.info(f"Encryption key: {encryption_key}")
                response['X-Encryption-Key'] = encryption_key
                # In your download view:

                logger.info("Encryption details:")
                with share_link.file.file.open('rb') as f:
                    content = f.read()
                    logger.info(f"First byte (version): {content[0]}")
                    logger.info(f"First 32 bytes: {content[:32]}")

                # Also add Access-Control-Expose-Headers to make custom header visible to JavaScript
                response['Access-Control-Expose-Headers'] = 'X-Encryption-Key'

            # Update access statistics
            share_link.access_count = F('access_count') + 1
            share_link.last_accessed = timezone.now()
            share_link.save()

            # Record access
            FileAccess.objects.create(
                file=share_link.file,
                accessed_by=request.user if request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                access_type='download',
                share_link=share_link
            )

            return response

        except ShareLink.DoesNotExist:
            return Response(
                {'error': 'Share link not found or expired'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=True, methods=['get'], url_path='access-history')
    def get_access_history(self, request, pk=None):
        """Get access history for a file"""
        try:
            file = self.get_object()
            
            # Get access history for the last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            access_history = file.accesses.filter(
                accessed_at__gte=thirty_days_ago
            ).order_by('-accessed_at')

            # Format the history data
            history_data = []
            for access in access_history:
                history_data.append({
                    'accessed_at': access.accessed_at,
                    'access_type': access.access_type,
                    'accessed_by': access.accessed_by.username if access.accessed_by else 'Anonymous',
                    'ip_address': access.ip_address,
                })

            return Response(history_data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def format_access_data(self, accesses):
        """Format access data by date"""
        data_by_date = {}
        for access in accesses:
            date = access.accessed_at.date()
            if date not in data_by_date:
                data_by_date[date] = {
                    'date': date.strftime('%Y-%m-%d'),
                    'views': 0,
                    'downloads': 0,
                    'unique_visitors': set()
                }
            
            if access.access_type == 'view':
                data_by_date[date]['views'] += 1
            else:
                data_by_date[date]['downloads'] += 1

            if access.accessed_by:
                data_by_date[date]['unique_visitors'].add(access.accessed_by.id)

        # Convert data to list and format unique visitors count
        formatted_data = []
        for date_data in data_by_date.values():
            formatted_data.append({
                'date': date_data['date'],
                'views': date_data['views'],
                'downloads': date_data['downloads'],
                'unique_visitors': len(date_data['unique_visitors'])
            })

        return sorted(formatted_data, key=lambda x: x['date'], reverse=True)

class ShareLinkViewSet(viewsets.ModelViewSet):
    serializer_class = ShareLinkSerializer
    permission_classes = [AllowAny]  # Since verify-password needs anonymous access

    def get_queryset(self):
        if self.action == 'verify_password':
            # For password verification, return all ShareLinks
            return ShareLink.objects.all()
        elif not self.request.user.is_authenticated:
            # For unauthenticated users on other actions, return empty queryset
            return ShareLink.objects.none()
        elif self.request.user.is_staff:
            # For staff users, return all ShareLinks
            return ShareLink.objects.all()
        else:
            # For authenticated non-staff users, return only their ShareLinks
            return ShareLink.objects.filter(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='verify-password')
    def verify_password(self, request, pk=None):
        try:
            # Get the share link directly using the token
            share_link = ShareLink.objects.get(token=pk)
            
            # Check if the share link is still valid
            if not share_link.is_valid():
                return Response(
                    {'error': 'This share link has expired or reached its maximum access limit'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            password = request.data.get('password')

            if not share_link.is_password_protected:
                return Response(
                    {'error': 'This link is not password protected'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if share_link.check_password(password):
                logger.info(f"Password verified for share link {share_link.id}")
                
                access_token = share_link.generate_access_token()
                return Response({'message': 'Password verified', 'access_token': access_token})

            return Response(
                {'error': 'Invalid password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        except ShareLink.DoesNotExist:
            return Response(
                {'error': 'Share link not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_permissions(self):
        """
        Override to ensure only appropriate actions are allowed
        """
        if self.action == 'verify_password':
            permission_classes = [AllowAny]
        else:
            permission_classes = [HasKeycloakRole(['user', 'admin'])]
        return [permission() for permission in permission_classes]