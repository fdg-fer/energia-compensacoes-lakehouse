# =========================================
# ETL CKAN – Compensações Energia (ANEEL)
# Destino: MinIO (Parquet – Bronze)
# Modo: MinIO-only (sem Postgres)
# Ano-alvo: 2025
# =========================================

import os
import json
import uuid
import logging
import requests
import pandas as pd

from dotenv import load_dotenv

import boto3
import pyarrow as pa
import pyarrow.parquet as pq


# =========================================
# CONFIG
# =========================================

load_dotenv()  # carrega .env da raiz do projeto

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

CKAN_BASE_URL = "https://dadosabertos.aneel.gov.br/api/3/action"
RID_COMP = "364d945e-a18b-4111-ab1b-73aa0f7b06b1"

BATCH = 50000
TIMEOUT = 60
ANO_ALVO = 2025

SIG_INDICADORES_COMP = [
    "PGUCAT",
    "PGUCBTNU",
    "PGUCBTU",
    "PGUCMTNU",
    "PGUCMTU"
]

# ---- MinIO ----
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin12345")
MINIO_BUCKET = os.getenv("MINIO_BUCKET_BRONZE", "energia-bronze")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

def ensure_bucket(bucket_name: str):
    """Cria o bucket se não existir (idempotente)."""
    existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
    if bucket_name not in existing:
        s3.create_bucket(Bucket=bucket_name)
        logging.info(f"Bucket criado: {bucket_name}")
    else:
        logging.info(f"Bucket já existe: {bucket_name}")


def upload_parquet_minio_partitioned(df: pd.DataFrame, dataset: str = "compensacoes"):
    """
    Grava compensações no MinIO particionadas por:
    - AnoIndice (ano)
    - NumPeriodoIndice (mês)
    
    Path:
    ckan/compensacoes/ano=YYYY/mes=MM/part-<uuid>.parquet
    """
    required = {"AnoIndice", "NumPeriodoIndice"}
    if not required.issubset(df.columns):
        raise ValueError(f"Faltam colunas obrigatórias: {required - set(df.columns)}")

    os.makedirs("tmp_parquet", exist_ok=True)

    for (ano, mes), g in df.groupby(["AnoIndice", "NumPeriodoIndice"], dropna=False):
        try:
            ano_i = int(ano)
            mes_i = int(mes)
        except Exception:
            continue

        file_id = uuid.uuid4().hex
        local_path = f"tmp_parquet/{dataset}_{ano_i}_{mes_i:02d}_{file_id}.parquet"

        table = pa.Table.from_pandas(g, preserve_index=False)
        pq.write_table(table, local_path)

        key = f"ckan/{dataset}/ano={ano_i}/mes={mes_i:02d}/part-{file_id}.parquet"
        s3.upload_file(local_path, MINIO_BUCKET, key)

        os.remove(local_path)



def load_compensacoes_ano(ano: int = 2025):
    logging.info(f"Iniciando carga de compensações para AnoIndice={ano}")
    ensure_bucket(MINIO_BUCKET)

    filtros = json.dumps({
        "SigIndicador": SIG_INDICADORES_COMP,
        "AnoIndice": str(ano)  # CKAN às vezes espera string
    })

    offset = 0
    total = 0

    while True:
        r = requests.get(
            f"{CKAN_BASE_URL}/datastore_search",
            params={
                "resource_id": RID_COMP,
                "limit": BATCH,
                "offset": offset,
                "filters": filtros
            },
            timeout=TIMEOUT
        )
        r.raise_for_status()

        rows = r.json()["result"].get("records", [])
        if not rows:
            break

        df = pd.DataFrame(rows)

        if "SigAgente" in df.columns:
            df["SigAgente"] = df["SigAgente"].astype(str).str.strip()

        upload_parquet_minio_partitioned(df, dataset="compensacoes")

        got = len(df)
        total += got
        offset += got
        logging.info(f"[compensacoes {ano}] +{got:,} (total {total:,})")

    logging.info(f"Finalizado. Total carregado ({ano}): {total:,} linhas")


if __name__ == "__main__":
    load_compensacoes_ano(ANO_ALVO)
