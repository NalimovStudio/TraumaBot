from pydantic import (
    BaseModel,
    SecretStr,
    RedisDsn,
    PostgresDsn
)


class RedisConfig(BaseModel):
    host: str
    port: int
    database: str = "0"
    username: str | None = None
    password: SecretStr | None = None

    def build_url(self) -> str:
        dsn: RedisDsn = RedisDsn.build(
            scheme="redis",
            username=self.username,
            password=self.password.get_secret_value() if self.password else None,
            host=self.host,
            port=self.port,
            path=self.database
        )
        return dsn.unicode_string()


class DatabaseConfig(BaseModel):
    user: str
    password: SecretStr
    path: str
    host: str = "db"
    port: int = 5432
    driver: str = "asyncpg"
    system: str = "postgresql"

    def build_connection_url(self) -> str:
        dsn: PostgresDsn = PostgresDsn.build(
            scheme=f"{self.system}+{self.driver}",
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password.get_secret_value(),
            path=self.path
        )
        return dsn.unicode_string()


class BotConfig(BaseModel):
    token: SecretStr


class AssistantConfig(BaseModel):
    api_key: SecretStr


class PaymentConfig(BaseModel):
    "Config for application YooKassa"

    store_id: SecretStr
    store_token: SecretStr
