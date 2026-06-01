from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # OpenAPI schema + Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/auth/', include('apps.users.urls')),
    path('api/users/', include('apps.users.profile_urls')),
    path('api/config/', include('apps.config.urls')),
    path('api/offers/', include('apps.offers.urls')),
    path('api/proposals/', include('apps.proposals.urls')),
    path('api/deals/', include('apps.deals.urls')),
    path('api/drops/', include('apps.drops.urls')),
    path('api/membership/', include('apps.membership.urls')),
    path('api/ratings/', include('apps.ratings.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/contracts/', include('apps.contracts.urls')),
    path('api/brands/', include('apps.brands.urls')),
    path('api/analytics/', include('apps.admin_panel.analytics_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
