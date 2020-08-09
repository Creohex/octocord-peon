"""Database entities."""

import time

import pymongo

from collections import MutableMapping
from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    OperationFailure,
    WTimeoutError,
)

from peon.utils import (
    get_env_vars,
    ENV_DB_USER,
    ENV_DB_PASS,
    ENV_DB_HOST,
)


class _Collection(object):
    """Wrapper over pymongo's collection object."""

    class CallProxy(object):
        """Wrapper for collection's methods."""

        def __init__(self, func, reconnect, timeout):
            self._func = func
            self._reconnect = reconnect
            self._timeout = timeout

        def __call__(self, *args, **kwargs):

            tries = self._reconnect
            error = None

            while True:
                try:
                    return self._func(*args, **kwargs)
                except (ConnectionFailure, AutoReconnect) as exc:
                    error = exc
                except WTimeoutError as exc:
                    error = exc
                    break

                if tries <= 1:
                    break

                time.sleep(self._timeout)
                tries -= 1

            raise error

    def __init__(self, collection, reconnect, timeout):
        self.__collection = collection
        self.__reconnect = reconnect
        self.__timeout = timeout

    def __getattr__(self, name):
        value = getattr(self.__collection, name)
        if callable(value):
            return self.CallProxy(value, self.__reconnect, self.__timeout)
        else:
            return value

    def __getitem__(self, name):
        return self.__collection[name]

    def __repr__(self):
        return "_Collection({0}, reconnect={1}, timeout={2})".format(
            self.__collection.name, self.__reconnect, self.__timeout)


class Database(object):
    """Wrapper over pymongo's database object."""

    def __init__(self, name, reconnect=0, timeout=1):
        """Database wrapper constructor."""

        self.__name = name
        self.__reconnect = reconnect
        self.__timeout = timeout
        self.__env_vars = get_env_vars()

        self.__database = self._connect()[self.__name]

    def _connect(self):
        """Returns a connection to MongoDB."""

        connection = pymongo.MongoClient("mongodb://{0}:{1}@{2}".format(
            self.__env_vars[ENV_DB_USER],
            self.__env_vars[ENV_DB_PASS],
            self.__env_vars[ENV_DB_HOST]))

        return connection

    def drop(self):
        """Alias method to self.client.drop_database(name)."""

        self.__database.client.drop_database(self.__name)

    def __getattr__(self, name):
        value = getattr(self.__database, name)
        if isinstance(value, pymongo.collection.Collection):
            return _Collection(value, self.__reconnect, self.__timeout)
        else:
            return value

    def __getitem__(self, name):
        return _Collection(self.__database[name], self.__reconnect, self.__timeout)

    def __repr__(self):
        return "Database({0}, reconnect={1}, timeout={2})".format(
            self.__database.name, self.__reconnect, self.__timeout)
