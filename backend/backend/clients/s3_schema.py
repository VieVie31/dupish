from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = []


class S3Settings(BaseSettings):
    # S3 credentials
    ACCESS_KEY_ID: str | None = None
    SECRET_ACCESS_KEY: SecretStr | None = None

    # S3 config
    REGION_NAME: str | None = None
    ENDPOINT_URL: str | None = None

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))
