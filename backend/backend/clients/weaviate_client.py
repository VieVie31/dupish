from functools import lru_cache

import weaviate

__all__ = ["get_weaviate_client"]


def _get_client(settings: "WeaviateSettings"):  # type: ignore
    return weaviate.connect_to_custom(
        http_host=settings.HTTP_HOST,
        http_port=settings.HTTP_PORT,
        http_secure=settings.HTTP_SECURE,
        grpc_host=settings.GRPC_HOST,
        grpc_port=settings.GRPC_PORT,
        grpc_secure=settings.GRPC_SECURE,
    )


@lru_cache
def get_weaviate_client(settings: "WeaviateSettings"):  # type: ignore
    from ..settings import WeaviateSettings

    return _get_client(settings)
