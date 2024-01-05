"""Database entities."""

from __future__ import annotations

from copy import deepcopy
from typing import Self
from datetime import datetime

from mongoengine import (
    connect as _connect,
    DateTimeField,
    disconnect,
    Document,
    IntField,
    DoesNotExist,
    DynamicField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    StringField,
)

from . import utils
from .exceptions import DocumentNotFound
from .utils import (
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

MAX_SAVED_GPT_INTERACTIONS = 100
"""Maximum amount of saved dialogues between user and GPT model."""


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


class BaseDocument(Document):
    """Abastract base document, defining common functionality."""

    meta = {
        "abstract": True,
        "db_alias": DB_PEON,
    }

    @classmethod
    def find_all(cls: Document) -> list[Self]:
        return cls.objects.all()

    @classmethod
    def find_one(cls: Document, **kwargs) -> Self:
        try:
            return cls.objects.get(**kwargs)
        except DoesNotExist:
            return None

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
    """Document for miscellaneous key-value pairs that have to stored in DB."""

    category = StringField(primary_key=True, unique=True, required=True)
    value = DynamicField(required=True)

    @classmethod
    def get_category(cls, category: str) -> Self:
        document = cls.objects(category=category).get()
        if not document:
            raise DocumentNotFound(f"Asset '{category}' not found!")
        return document

    @classmethod
    def load_assets(cls, categories: list) -> None:
        for c in categories:
            setattr(utils, c, cls.get_category(c).value)


class GPTRoleSetting(BaseDocument):
    """Represents GPT personalization for specific owner(user)."""

    owner_id = StringField(unique=True, required=True)
    role_description = StringField(required=True)

    @classmethod
    def get(cls, owner_id: str) -> Self:
        return cls.find_one(owner_id=owner_id)

    @classmethod
    def set(cls, owner_id: str, role_description: str) -> bool:
        cls(owner_id=owner_id).find_one().delete()
        cls(owner_id=owner_id, role_description=role_description).save()


class GPTChatInteraction(EmbeddedDocument):
    """Represents a single interaction between a user and GPT model."""

    user_message = StringField(required=True)
    system_reply = StringField(required=True)
    timestamp = DateTimeField(required=True, default=lambda: datetime.now())


class GPTChatHistory(BaseDocument):
    """
    Represents histories of interactions between different users and GPT model.

    Structure:
    {
        "owner_id": str,
        "interactions": [
            {
                "user_message": str,
                "system_reply": str,
                "timestamp": int,
            },
            <...>,
        ],
        <...>,
    }
    """

    owner_id = StringField(unique=True, required=True)
    interactions = ListField(
        EmbeddedDocumentField(GPTChatInteraction), max_length=MAX_SAVED_GPT_INTERACTIONS
    )

    @classmethod
    def store(cls, owner_id: str, user: str, system: str, timestamp: int = None) -> None:
        """Stores an interaction for specific owner ID."""

        document = cls.find_one(owner_id=owner_id)
        interaction = GPTChatInteraction(
            user_message=user,
            system_reply=system,
            timestamp=timestamp,
        )
        if document:
            if len(document.interactions) >= MAX_SAVED_GPT_INTERACTIONS:
                document.interactions.pop(0)
            document.interactions.append(interaction)
            document.save()
        else:
            cls(owner_id=owner_id, interactions=[interaction]).save()

    @classmethod
    def fetch(cls, owner_id: str) -> list:
        """
        Fetches sequence of interactions in format (as expected by OpenAI Completion):
        [
            {"role": "user", "content": <...>},
            {"role": "assistant", "content": <...>},
            {"role": "user", "content": <...>},
            {"role": "assistant", "content": <...>},
            <...>
        ]
        """

        document = cls.find_one(owner_id=owner_id)
        if document:
            # data = document.interactions.sort(key=lambda r: r.timestamp)
            # FIXME: make sure interactions are in the correct order
            #        (or sort them otherwise)
            data = document.interactions
            formatted = []
            for d in data:
                formatted.append({"role": "user", "content": d.user_message})
                formatted.append({"role": "assistant", "content": d.system_reply})
            return formatted
        else:
            return []
