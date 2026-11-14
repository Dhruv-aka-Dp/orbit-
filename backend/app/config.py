from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ORBIT_", extra="ignore")

    env: str = "development"
    database_url: str = "sqlite:///./orbit.db"
    cors_origins: str = "http://localhost:8080"
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_client_id: str | None = None
    oidc_redirect_uri: str | None = None
    openai_model: str | None = None
    allow_dev_auth: bool = True

    @property
    def production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.production and (settings.allow_dev_auth or not settings.oidc_issuer or not settings.oidc_audience or not settings.oidc_client_id or not settings.oidc_redirect_uri):
        raise RuntimeError("Production requires OIDC issuer, audience, client ID, redirect URI and ORBIT_ALLOW_DEV_AUTH=false.")
    return settings

