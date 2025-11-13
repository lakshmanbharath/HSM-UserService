import boto3
from django.conf import settings
from urllib.parse import urlparse, unquote


def generate_presigned_url_from_object_url(
    object_url: str, expiration: int = 3600
) -> str:
    """
    Converts an S3 object URL into a presigned URL for secure access.
    """
    s3_key = extract_s3_key_from_url(object_url)
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": s3_key,
            "ResponseContentDisposition": "inline",
            "ResponseContentType": "application/pdf",
        },
        ExpiresIn=expiration,
    )


def extract_s3_key_from_url(object_url: str) -> str:
    """
    Extracts the S3 object key from a full S3 URL.
    Handles URL encoding and nested folder structures.
    """
    parsed_url = urlparse(object_url)
    object_key = unquote(parsed_url.path.lstrip("/"))
    return object_key
