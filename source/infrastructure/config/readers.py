from .models import DatabaseConfig, BotConfig, RedisConfig, AssistantConfig, PaymentConfig

from environs import Env

def get_database_config(env: Env) -> DatabaseConfig:
    return DatabaseConfig(
        user=env.str("DB_USER"),
        password=env.str("DB_PASSWORD"),
        host=env.str("DB_HOST", "db"),
        port=env.int("DB_PORT", 5432),
        path=env.str("DB_PATH"),
        driver=env.str("DB_DRIVER", "asyncpg"),
        database_system=env.str("DB_SYSTEM", "postgresql"),
    )

def get_bot_config(env: Env) -> BotConfig:
    return BotConfig(
        token=env.str("TELEGRAM_TOKEN")
    )

def get_redis_config(env: Env) -> RedisConfig:
    return RedisConfig(
        port=env.int("REDIS_PORT"),
        host=env.str("REDIS_HOST"),
        password=env.str("REDIS_PASSWORD", None),
        database=env.str("REDIS_DATABASE", "0")
    )

def get_assistant_config(env: Env) -> AssistantConfig:
    return AssistantConfig(
        api_key=env.str("ASSISTANT_API_KEY", "")
    )

def get_payment_config(env: Env) -> PaymentConfig:
    return PaymentConfig(
        store_id=env.str("STORE_ID", ""),
        store_token=env.str("STORE_TOKEN", "")
    )