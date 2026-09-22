from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.tenants.urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/academics/", include("apps.academics.urls")),
    path("api/people/", include("apps.people.urls")),
    path("api/teaching/", include("apps.teaching.urls")),
    path("api/assessments/", include("apps.assessments.urls")),
    path("api/report-cards/", include("apps.report_cards.urls")),
    path("api/finance/", include("apps.finance.urls")),
    path("api/whatsapp-ai/", include("apps.whatsapp_ai.urls")),
    path("api/public/report-cards/", include("apps.report_cards.public_urls")),
    path("verify/report-card/", include("apps.report_cards.verify_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
