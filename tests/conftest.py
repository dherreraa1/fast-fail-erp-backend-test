import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from app.models import Company

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass", email="test@example.com")

@pytest.fixture
def company(db):
    return Company.objects.create(name="Test Company")

@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

# Mock para las funciones de S3 
@pytest.fixture(autouse=True)
def mock_s3_functions(monkeypatch):
    """Mock S3 functions to avoid external dependencies during testing"""
    def mock_presigned_put(key, expires_in=None):
        return f"https://test-bucket.s3.amazonaws.com/{key}?AWSAccessKeyId=test&Signature=test&Expires=test"
    
    def mock_presigned_get(key, expires_in=None):
        return f"https://test-bucket.s3.amazonaws.com/{key}?AWSAccessKeyId=test&Signature=test&Expires=test"
    
    monkeypatch.setattr("app.storage.generate_presigned_put_url", mock_presigned_put)
    monkeypatch.setattr("app.storage.generate_presigned_get_url", mock_presigned_get)