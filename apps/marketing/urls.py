from django.urls import path
from django.views.generic import TemplateView

app_name = "marketing"
urlpatterns = [
    path(
        "mentions-legales/",
        TemplateView.as_view(template_name="marketing/legal_notice.html"),
        name="legal_notice",
    ),
    path(
        "confidentialite/",
        TemplateView.as_view(template_name="marketing/privacy.html"),
        name="privacy",
    ),
]
