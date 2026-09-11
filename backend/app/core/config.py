from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AUTOPACKLINE API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "mysql+pymysql://autopackline:autopackline@mysql:3306/autopackline"
    cors_origins: str = "http://localhost:5173"
    jwt_secret: str = "change-me"
    jwt_exp_minutes: int = 480
    initial_admin_username: str = "admin"
    initial_admin_name: str = "Administrador AUTOPACKLINE"
    initial_admin_password: str = "Autopack@2026"
    plc_simulator_timeout_seconds: int = 5
    plc_retry_max_attempts: int = 3
    plc_retry_interval_seconds: int = 1
    plc_physical_enabled: bool = False
    plc_modbus_host: str = "192.168.0.2"
    plc_modbus_port: int = 502
    plc_modbus_unit_id: int = 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
