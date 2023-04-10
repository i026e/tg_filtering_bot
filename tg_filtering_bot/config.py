from typing import Union

from pydantic import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        secrets_dir = '/var/run/tg_filtering_bot'

    # Get it from https://my.telegram.org/apps
    LISTENER_API_ID: str
    LISTENER_API_HASH: str
    LISTENER_API_NAME: str

    LISTENER_CHANNEL_ID: Union[str, int]
    LISTENER_CHANNEL_NAME: str = ""  # Optional
    LISTENER_LOAD_PREV_MESSAGES: int = 10

    BOT_TOKEN: str

    SQLALCHEMY_DATABASE_URI: str = "sqlite+aiosqlite:///tg_filtering_bot.db"

    QUEUE_SIZE = 1024
    DEBUG: bool = False


settings = Settings()