"""
Application configuration.

We use pydantic-settings to read values from environment variables (or a .env file).
This keeps secrets like the database password OUT of the source code.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Where to connect to the database. Defaults to local Postgres.
    DATABASE_URL: str = "postgresql://postgres:skynet123@localhost:5432/skynet"

    # Turn on extra debug info during development.
    DEBUG: bool = True

    # Tells pydantic-settings to also load values from a .env file if present.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# A single shared settings instance the rest of the app imports.
settings = Settings()
