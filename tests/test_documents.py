import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_upload_document_creates_metadata(auth_client, company):
    url = reverse("documents-list")
    payload = {
        "company_id": str(company.id),
        "entity": {"entity_type": "vehicle", "entity_id": "00000000-0000-0000-0000-000000000000"},
        "document": {
            "name": "soat.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 123456,
            "bucket_key": f"companies/{company.id}/docs/soat.pdf",
        },
        "validation_flow": {"enabled": False}
    }
    response = auth_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "upload_url" in response.data
