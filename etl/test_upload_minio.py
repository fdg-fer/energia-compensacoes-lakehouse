import os
import pandas as pd
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import uuid

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin12345")
BUCKET = os.getenv("MINIO_BUCKET_BRONZE", "energia-bronze")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

df = pd.DataFrame({"a":[1,2,3], "b":["x","y","z"]})

os.makedirs("tmp_parquet", exist_ok=True)
file_id = uuid.uuid4().hex
local_path = f"tmp_parquet/test_{file_id}.parquet"
pq.write_table(pa.Table.from_pandas(df, preserve_index=False), local_path)

key = f"tests/test_{file_id}.parquet"
s3.upload_file(local_path, BUCKET, key)
print(f"OK: s3://{BUCKET}/{key}")

os.remove(local_path)
