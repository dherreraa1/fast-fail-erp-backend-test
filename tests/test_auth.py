import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_obtain_jwt_token(client, user):
    url = reverse("token_obtain_pair")
    response = client.post(url, {"username": "testuser", "password": "testpass"}, format="json")
    assert response.status_code == 200
    assert "access" in response.data
