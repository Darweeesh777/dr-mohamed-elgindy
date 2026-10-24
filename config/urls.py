from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Uploaded files are served by Django only in development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Public pages live under a language prefix: /ar/ and /en/.
urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    prefix_default_language=True,
)
