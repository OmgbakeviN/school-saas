from django.urls import path

from .views import PublicReportCardVerificationPageView


urlpatterns = [
    path(
        "<str:token>/",
        PublicReportCardVerificationPageView.as_view(),
        name="report-card-verification-page",
    ),
]
