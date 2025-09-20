import pytest
from django.urls import reverse
from rest_framework import status
from app.models import Document, ValidationStep

@pytest.mark.django_db
def test_validation_flow_approval(auth_client, company, user):
    doc = Document.objects.create(
        company=company,
        entity_type="vehicle",
        entity_id="00000000-0000-0000-0000-000000000000",
        name="cert.pdf",
        mime_type="application/pdf",
        size_bytes=5000,
        bucket_key="companies/x/docs/cert.pdf",
        validation_status="P",
        created_by=user,
    )
    ValidationStep.objects.create(document=doc, order=1, approver=user)
    url = reverse("documents-approve", args=[doc.id])
    response = auth_client.post(url, {"actor_user_id": str(user.id)}, format="json")
    doc.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert doc.validation_status == "A"
