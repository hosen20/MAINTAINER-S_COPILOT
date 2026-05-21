from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.domain.errors import InfrastructureError
from app.infra.settings import Settings
from app.infra.vault import AppSecrets


def make_minio_client(settings: Settings, secrets: AppSecrets) -> Minio:
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=secrets.minio_access_key,
        secret_key=secrets.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket(client: Minio, bucket: str) -> None:
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except S3Error as exc:
        raise InfrastructureError(f"MinIO bucket check failed: {exc}") from exc


def put_text(client: Minio, bucket: str, object_name: str, content: str) -> None:
    data = content.encode("utf-8")
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=BytesIO(data),
        length=len(data),
        content_type="text/plain",
    )