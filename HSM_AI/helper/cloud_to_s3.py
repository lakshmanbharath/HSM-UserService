import io
import base64
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from django.conf import settings


def upload_base64_to_s3(file_content_base64: str, file_name: str, project_name: str) -> str:
    """
    Universal helper:
      - Decodes base64 file content
      - Ensures S3 bucket + project folder exist
      - Uploads file to S3
      - Returns public S3 URL
    """
    # Decode base64 → bytes
    file_bytes = base64.b64decode(file_content_base64)

    # Ensure bucket
    _ensure_s3_bucket_exists()

    # Ensure project folder
    _ensure_project_folder_exists(project_name)

    # Upload file
    return _upload_bytes_to_s3(file_bytes, file_name, project_name)

def _ensure_s3_bucket_exists():
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME.lower().replace("_", "-")
    region = settings.AWS_S3_REGION_NAME

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region,
    )

    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ["404", "NoSuchBucket"]:
            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
        else:
            raise

def _ensure_project_folder_exists(project_name: str):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region = settings.AWS_S3_REGION_NAME
    folder_prefix = f"{project_name}/"

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region,
    )

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix, MaxKeys=1)
    if "Contents" not in response:
        s3.put_object(Bucket=bucket_name, Key=f"{folder_prefix}.keep")

def _upload_bytes_to_s3(file_bytes: bytes, file_name: str, project_name: str) -> str:
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region = settings.AWS_S3_REGION_NAME
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    folder_prefix = f"{project_name}/{project_name}-{timestamp}/"
    s3_key = f"{folder_prefix}{file_name}"

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region,
    )

    file_obj = io.BytesIO(file_bytes)

    try:
        s3.upload_fileobj(
            file_obj,
            bucket_name,
            s3_key,
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )
        print(f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}", "s3_key")
        return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
    except ClientError as e:
        raise
