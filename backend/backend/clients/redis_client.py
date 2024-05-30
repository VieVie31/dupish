from functools import lru_cache

import redis

__all__ = ["get_redis_client"]


def _get_client(settings: "RedisSettings", decode_response: bool):  # type: ignore
    return redis.Redis(
        host=settings.DOMAIN,
        port=settings.PORT,
        password=settings.PASSWORD.get_secret_value(),
        decode_responses=decode_response,
    )


@lru_cache
def get_redis_client(settings: "RedisSettings", decode_response: bool):  # type: ignore
    from ..settings import RedisSettings

    return _get_client(settings, decode_response)
