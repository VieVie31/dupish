from functools import lru_cache

import boto3
from pydantic import SecretStr

from .s3_schema import S3Settings

__all__ = ["get_s3_client"]


def _get_client(service, settings: S3Settings):
    return boto3.client(
        service,
        aws_access_key_id=settings.ACCESS_KEY_ID,
        aws_secret_access_key=(
            settings.SECRET_ACCESS_KEY.get_secret_value()
            if isinstance(settings.SECRET_ACCESS_KEY, SecretStr)
            else None
        ),
        region_name=settings.REGION_NAME,
        endpoint_url=settings.ENDPOINT_URL,
    )


@lru_cache
def get_s3_client(settings: S3Settings):
    return _get_client("s3", settings)
