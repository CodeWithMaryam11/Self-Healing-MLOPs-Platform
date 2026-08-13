import os
import boto3
from botocore.exceptions import ClientError
from io import BytesIO

# Default to the Docker network URL if running in Docker, or localhost if running locally
MINIO_URL = os.environ.get("MINIO_URL", "http://localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

# The root bucket name for our multi-tenant SaaS
DATASETS_BUCKET = "pipelineiq-datasets"

# Create a boto3 client pointing to our local MinIO container
s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_URL,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1"
)

def ensure_bucket_exists():
    """Ensure the datasets bucket exists in MinIO."""
    try:
        s3_client.head_bucket(Bucket=DATASETS_BUCKET)
    except ClientError:
        # Bucket does not exist, create it
        s3_client.create_bucket(Bucket=DATASETS_BUCKET)

def upload_dataset_to_s3(user_id: str, filename: str, file_bytes: bytes) -> str:
    """Uploads a user's dataset to MinIO/S3 and returns the S3 object key."""
    import socket
    from urllib.parse import urlparse
    parsed = urlparse(MINIO_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 9000
    
    # Fast check if MinIO is listening
    with socket.create_connection((host, port), timeout=0.5):
        ensure_bucket_exists()
        object_key = f"{user_id}/{filename}"
        s3_client.upload_fileobj(
            BytesIO(file_bytes),
            DATASETS_BUCKET,
            object_key
        )
        return object_key

def download_dataset_from_s3(object_key: str) -> bytes:
    """Downloads a dataset from MinIO/S3 into memory."""
    file_stream = BytesIO()
    s3_client.download_fileobj(DATASETS_BUCKET, object_key, file_stream)
    return file_stream.getvalue()
