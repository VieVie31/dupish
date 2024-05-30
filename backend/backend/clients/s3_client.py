from functools import lru_cache
from typing import Union

import boto3
from botocore.exceptions import ClientError
from pydantic import SecretStr

from .s3_schema import S3Settings

__all__ = ["get_s3_client", "generate_presigned_url"]


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


def generate_presigned_url(
    s3_client, bucket_name: str, s3_key: str, expiration: int = 3600
) -> Union[str, None]:
    """Generate a presigned URL for a specified S3 object.

    Args:
        bucket_name (str): The name of the S3 bucket.
        object_name (str): The name of the S3 object.
        expiration (int, optional): The number of seconds the URL should be valid for. Defaults to 3600 (1 hour).

    Returns
        str: The presigned URL for the S3 object.

    """
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": s3_key},
            ExpiresIn=expiration,
        )
        return response
    except ClientError as e:
        return None
