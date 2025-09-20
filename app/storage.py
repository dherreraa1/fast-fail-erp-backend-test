from typing import Optional
import boto3
from botocore.client import Config
from django.conf import settings

def get_s3_client():
    endpoint = getattr(settings, "AWS_S3_ENDPOINT", None)
    client_kwargs = {
        "region_name": settings.AWS_REGION,
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "config": Config(signature_version="s3v4"),
    }
    if endpoint:
        client_kwargs["endpoint_url"] = endpoint
    return boto3.client("s3", **client_kwargs)

def generate_presigned_put_url(key: str, expires_in: Optional[int] = None) -> str:
    if expires_in is None:
        expires_in = int(getattr(settings, "AWS_PRESIGNED_EXPIRATION", 3600))
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )

def generate_presigned_get_url(key: str, expires_in: Optional[int] = None) -> str:
    if expires_in is None:
        expires_in = int(getattr(settings, "AWS_PRESIGNED_EXPIRATION", 3600))
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )
