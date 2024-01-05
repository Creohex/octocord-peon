"""Various utils."""

import logging
import os
import sys


ENV_TOKEN_DISCORD = "discord_token"
ENV_TOKEN_TELEGRAM = "telegram_token"
ENV_TOKEN_RAPIDAPI = "rapidapi_token"
ENV_TOKEN_STEAMAPI = "steamapi_token"
ENV_TOKEN_OPENAI = "openai_token"
ENV_TWITCH_CLIENT_ID = "twitch_client_id"
ENV_TWITCH_CLIENT_SECRET = "twitch_client_secret"
ENV_TELEGRAM_ADMINS = "telegram_admins"
ENV_DB_ENABLED = "DB_ENABLED"
ENV_DB_HOST = "MONGO_HOST"
ENV_DB_PORT = "MONGO_PORT"
ENV_DB_USER = "MONGO_INITDB_ROOT_USERNAME"
ENV_DB_PASS = "MONGO_INITDB_ROOT_PASSWORD"
ENV_VARS = [
    ENV_TOKEN_DISCORD,
    ENV_TOKEN_TELEGRAM,
    ENV_TOKEN_RAPIDAPI,
    ENV_TOKEN_STEAMAPI,
    ENV_TWITCH_CLIENT_ID,
    ENV_TWITCH_CLIENT_SECRET,
    ENV_DB_ENABLED,
    ENV_DB_HOST,
    ENV_DB_PORT,
    ENV_DB_USER,
    ENV_DB_PASS,
]
"""Required environment variables."""

ASSETS_FOLDER = "/app/assets"
"""Assets folder location (docker container)."""

APP_NAME = "octocord"


def get_env_vars():
    """Check if required env vars are set and return dict containing them."""

    missing_variables = [_ for _ in ENV_VARS if _ not in os.environ.keys()]
    if len(missing_variables):
        raise Exception(f"Error: missing required variables: {missing_variables}")

    return {key: os.environ[key] for key in ENV_VARS}


def get_env_var(key):
    """Retrieves a single env var."""

    value = os.environ.get(key)
    if value is None:
        raise Exception(f"Error: env var '{key}' is not set!")
    return value


def get_file(name, mode="rb"):
    """Returns existing file as bytes."""

    return open(f"{ASSETS_FOLDER}/{name}", mode).read()


def logger(level: str = None) -> logging.Logger:
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(level or logging.INFO)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logging.getLogger(APP_NAME)
