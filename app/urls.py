from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, CompanyCreateView

router = DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="documents")

urlpatterns = router.urls + [
    path("companies/", CompanyCreateView.as_view(), name="companies-create"),
]