"""Database entities."""

import time

from umongo import Instance, Document, fields, validate

from peon.utils import (
    get_db,
    get_env_vars,
    ENV_DB_USER,
    ENV_DB_PASS,
    ENV_DB_HOST,
)


env_vars = get_env_vars()
DB_NAME = "peondb"

instance = Instance(get_db(
    env_vars[ENV_DB_HOST], env_vars[ENV_DB_USER], env_vars[ENV_DB_PASS], DB_NAME))


def check_connection(db_name="conn_check"):
    """Verify that db is accessible."""

    try:
        db = get_db(
            env_vars[ENV_DB_HOST], env_vars[ENV_DB_USER], env_vars[ENV_DB_PASS],
            "test_db"
        )
        db["test_collection"].insert({"test_field": "test_value"})
        db["test_collection"].drop()
    except:
        import traceback
        traceback.print_exc()
        return False

    return True


@instance.register
class Message(Document):
    """Test mongo entity."""

    test_field = fields.StringField(required=False)

    class Meta:
        collection_name = "test_collection"
