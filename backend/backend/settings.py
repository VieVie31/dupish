import yaml
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .clients import S3Settings

__all__ = ["env_settings", "broker_settings", "s3_settings"]


class WeaviateSettings(BaseSettings):
    HTTP_HOST: str
    HTTP_PORT: int
    HTTP_SECURE: bool
    GRPC_HOST: str
    GRPC_PORT: int
    GRPC_SECURE: bool

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class S3Settings(S3Settings):
    BUCKET_MEDIA: str


class RedisSettings(BaseSettings):
    USERNAME: str
    PASSWORD: SecretStr
    DOMAIN: str
    PORT: int

    @property
    def REDIS_URL(self):
        return f"redis://{self.USERNAME}:{self.PASSWORD.get_secret_value()}@{self.DOMAIN}:{self.PORT}/0"

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class EnvSettings(BaseSettings):
    s3: S3Settings
    weaviate: WeaviateSettings
    redis: RedisSettings

    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            ".env.dev",
            ".env.prod",
            "../.env",
            "/usr/src/.env",
        ),
        env_nested_delimiter="__",
    )


env_settings = EnvSettings()  # pyright: ignore
s3_settings = env_settings.s3
weaviate_settings = env_settings.weaviate
redis_settings = env_settings.redis
