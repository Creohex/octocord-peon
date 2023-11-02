"""Database entities."""

from __future__ import annotations

from copy import deepcopy
from mongoengine import (
    connect as _connect,
    disconnect,
    Document,
    DynamicField,
    IntField,
    StringField,
)

from . import utils
from .exceptions import DocumentNotFound
from .utils import (
    ASSET_CATEGORIES,
    ENV_DB_HOST,
    ENV_DB_PASS,
    ENV_DB_PORT,
    ENV_DB_USER,
    get_env_var,
)


DB_PEON = "peon_db"
DB_TEST = "test_db"
DATABASES = [DB_PEON, DB_TEST]
"""Database name definitions."""

CONNECTIONS = {db: None for db in DATABASES}
"""Globally stored connections to databases."""

OPTIONS_DEFAULT = {
    "authMechanism": "DEFAULT",
}
"""Default database connection options."""


def conn_string() -> str:
    """Compose MongoDB connection string."""

    return (
        f"mongodb://{get_env_var(ENV_DB_USER)}:{get_env_var(ENV_DB_PASS)}@"
        f"{get_env_var(ENV_DB_HOST)}:{get_env_var(ENV_DB_PORT)}"
    )


def mongodb_conn_uri(options=None) -> str:
    """Compose extended MongoDB connection URI to specific db and arbitrary options."""

    options = options or OPTIONS_DEFAULT
    options_composed = "&".join(f"{k}={v}" for k, v in (options or {}).items())
    return f"{conn_string()}{f'/?{options_composed}' if options_composed else ''}"


def connect(specific=None) -> None:
    """Establish connections to databases."""

    for db in [specific] if specific else DATABASES:
        if CONNECTIONS[db] is None:
            CONNECTIONS[db] = _connect(alias=db, db=db, host=mongodb_conn_uri())


def disconnect():
    """Drop DB connections."""

    for _, conn in CONNECTIONS.items():
        try:
            conn.disconnect()
        except:
            pass


def check_connection():
    """Attempt connection to a database."""

    try:
        print("Checking connection...")
        connect(specific=DB_TEST)
        entity = TestEntity(test_field="123")
        entity.save()
        entity.delete()
        TestEntity.drop_collection()
    except:
        return False
    finally:
        disconnect()

    return True


def initialize_db():
    connect(specific=DB_PEON)
    Assets.load_assets(ASSET_CATEGORIES)


class BaseDocument(Document):
    meta = {"abstract": True}

    @classmethod
    def all(cls: Document) -> list[Document]:
        return cls.objects.all()

    @classmethod
    def delete_all(cls):
        cls.objects().delete()

    def to_dict(self):
        data = deepcopy(self._data)
        data.pop("id")
        return data


class TestEntity(BaseDocument):
    meta = {"db_alias": DB_TEST}
    test_field = StringField()


class Assets(BaseDocument):
    meta = {"db_alias": DB_PEON}
    category = StringField()
    value = DynamicField()

    @classmethod
    def get_category(cls, category):
        document = cls.objects(category=category).get()
        if not document:
            raise DocumentNotFound(f"Asset '{category}' not found!")
        return document

    @classmethod
    def load_assets(cls, categories):
        for c in categories:
            setattr(utils, c, cls.get_category(c).value)
