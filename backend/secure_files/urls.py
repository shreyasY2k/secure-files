from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter

from secure_files.apps.files.views import FileViewSet, ShareLinkViewSet
from secure_files.apps.core.views import AdminViewSet

# Create main router
router = DefaultRouter()
router.register(r'files', FileViewSet, basename='file')
router.register(r'admin', AdminViewSet, basename='admin')
router.register(r'sharelinks', ShareLinkViewSet, basename='sharelink')

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/', include(router.urls)),
    
    # Authentication URLs
    path('api/auth/', include('rest_framework.urls')),
    
    # Explicit shared file path
    path(
        'api/files/shared/<str:token>/',
        FileViewSet.as_view({'get': 'get_shared_file'}),
        name='shared-file'
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)