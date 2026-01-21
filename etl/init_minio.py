import boto3
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin12345")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

BUCKETS = [
    "energia-bronze",
    "energia-silver",
    "energia-gold",
    "energia-logs",
]

existing = {b["Name"] for b in s3.list_buckets()["Buckets"]}

for bucket in BUCKETS:
    if bucket not in existing:
        s3.create_bucket(Bucket=bucket)
        print(f"Bucket criado: {bucket}")
    else:
        print(f"Bucket já existe: {bucket}")
