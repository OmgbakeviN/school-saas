from django.urls import path

from .views import PublicReportCardVerificationView


urlpatterns = [
    path(
        "verify/<str:token>/",
        PublicReportCardVerificationView.as_view(),
        name="public-report-card-verification",
    ),
]
