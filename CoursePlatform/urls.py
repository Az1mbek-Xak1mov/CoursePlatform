"""
URL configuration for CoursePlatform project.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve


def health_check(request):
    """Simple health check endpoint for container orchestration."""
    return JsonResponse({'status': 'healthy'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('accounts/', include('allauth.urls')),  # Django allauth (Google OAuth)
    path('', include('users.urls')),
    path('courses/', include('courses.urls')),
]

# Always serve media files (for both development and production without nginx)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Serve static files in development (WhiteNoise handles this in production)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Add debug toolbar in development
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

