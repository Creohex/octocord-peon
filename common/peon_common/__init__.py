"""Peon common entities."""

from peon_common.db import (
    Database,
    MongoObject,
    Document,
)

__all__ = [Database.__name__,
           MongoObject.__name__,
           Document.__name__]
