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


def check_connection(db_name="conn_check"):
    """Verify that db is accessible."""

    try:
        db = Database(db_name)
        db["{0}_test_coll".format(db_name)].insert({"bla": "bla"})
        db.drop()
    except:
        return False

    return True


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


class MongoObject(MutableMapping):
    """Represents document in MongoDB collection.

    Extends 'MutableMapping' abstract class for inherit dict-like behavior.
    Provides accessing sub-document fields in dot-notation like queries in MongoDB.
    """

    __object__ = None
    """Object dictionary."""

    def __init__(self, data=None):
        self.__object__ = data or {}
        for key in self.__object__:
            if isinstance(self.__object__[key], dict):
                self.__object__[key] = MongoObject(self.__object__[key])

    def __getitem__(self, key):
        if "." in key:
            key, rest = key.split(".", 1)
            return MongoObject(self.__object__[key]).__getitem__(rest)
        elif (
            key in self.__object__ and
            isinstance(self.__object__[key], dict)
        ):
            return MongoObject(self.__object__[key])
        else:
            return self.__object__[key]

    def __setitem__(self, key, value):
        if "." in key:
            key, rest = key.split(".", 1)
            self.__object__.setdefault(key, MongoObject()).__setitem__(rest, value)
        elif isinstance(value, dict):
            self.__object__[key] = MongoObject(value)
        else:
            self.__object__[key] = value

    def __delitem__(self, key):
        if "." in key:
            key, rest = key.split(".", 1)
            return MongoObject(self.__object__[key]).__delitem__(rest)
        else:
            del self.__object__[key]

    def __contains__(self, key):
        if "." in key:
            key, rest = key.split(".", 1)
            return MongoObject(self.__object__[key]).__contains__(rest)
        else:
            return key in self.__object__

    def __iter__(self):
        return iter(self.__object__)

    def __len__(self):
        return len(self.__object__)

    def __str__(self):
        return str(self.__object__)

    def __repr__(self):
        return "MongoObject(%s)" % (self.__object__,)

    def __del__(self):
        del self.__object__

    def to_dict(self):
        """Returns dict from MongoObject."""

        result = {}
        for key in self.__object__:
            if isinstance(self.__object__[key], MongoObject):
                result[key] = self[key].to_dict()
            else:
                result[key] = self.__object__[key]

        return result


class Document(MongoObject):
    """Represent JSON document."""

    __database__ = None
    __collection__ = None
    """Database connection properties."""

    primary_key = "_id"
    """Defines default primary field for query."""

    reconnect_amount = 5
    reconnect_timeout = 1
    """Connection parameters."""

    @classmethod
    def __check_definition(cls):
        """Ensures that document defined properly."""

        if cls.__database__ is None or cls.__collection__ is None:
            raise Exception("Missing __database__ / __collection__.")

    def __init__(self, data=None):
        super(Document, self).__init__(data)
        self.__check_definition()

    def __hash__(self):
        if self.primary_key not in self:
            raise TypeError(
                "A Document is not hashable if it is not saved. "
                "Save the document before hashing it."
            )
        return hash(self.id)

    @property
    def id(self):
        """The document's primary key value."""

        return self.get(self.primary_key)

    @classmethod
    def database(cls, reconnect=reconnect_amount, timeout=reconnect_timeout):
        """Returns database proxy."""

        cls.__check_definition()
        return Database(cls.__database__, reconnect=reconnect, timeout=timeout)

    @classmethod
    def collection(cls, reconnect=5, timeout=1):
        """Returns database collection proxy."""

        return cls.database(reconnect=reconnect, timeout=timeout)[cls.__collection__]

    @classmethod
    def create_index(cls):
        """Creates index by primary key.

        Must be overrided in subclasses for index creation
        """

        cls.collection().create_index(
            [(cls.primary_key, pymongo.ASCENDING),], unique=True)

    @classmethod
    def insert_many(cls, docs):
        """Inserts many documents into collection at once.

        :param docs: iterable objects with dics or Documents
        """

        objects = (
            doc.to_dict() if isinstance(doc, MongoObject) else doc
            for doc in docs
        )
        return cls.collection().insert_many(objects).inserted_ids

    @classmethod
    def one(cls, key=None, fields=None, required=True, add_query=None, **kwargs):
        """Returns one document from collection by key or optional query.

        Must be overrided in subclasses for custom queries.

        :param key: primary key value
        :param fields: document fields to return
        :param required: raise error if document not found
        :param add_query: optional query

        :returns: an instance of Document
        """

        query = {}
        if key:
            query[cls.primary_key] = key
        if add_query:
            query.update(add_query)

        data = cls.collection().find_one(query, projection=fields, **kwargs)
        if not data and required:
            raise cls.NotFound(key)

        return cls(data)

    @classmethod
    def all(cls, keys=None, fields=None, sort=None, add_query=None, **kwargs):
        """Returns list of documents form collection by keys and optional query.

        Must be overrided in subclasses for custom queries.

        :param keys: iterable of primary keys
        :param fields: document fields to return
        :param sort: optional sort
        :param add_query: optional query

        :returns: generator on Document instances
        """

        query = {}

        if keys is not None:
            query.update({cls.primary_key: {"$in": keys}})

        query.update(add_query or {})

        found = cls.collection().find(query, projection=fields, **kwargs)
        if sort:
            found.sort(sort)

        for data in found:
            yield cls(data)

    @classmethod
    def count(cls, query=None):
        """Returns documents count in collection by specified query.

        :param query: additional query
        """

        return cls.collection().count_documents(query or {})

    @classmethod
    def find(cls, *args, **kwargs):
        """Proxy for pymongo 'find' method."""

        return cls.collection().find(*args, **kwargs)

    @classmethod
    def find_one(cls, *args, **kwargs):
        """Proxy for pymongo 'find_one' method."""

        return cls.collection().find_one(*args, **kwargs)

    @classmethod
    def find_one_and_update(cls, *args, **kwargs):
        """Proxy for pymongo 'find_one_and_update' method."""

        return cls.collection().find_one_and_update(*args, **kwargs)

    @classmethod
    def find_one_and_replace(cls, *args, **kwargs):
        """Proxy for pymongo 'find_one_and_replace' method."""

        return cls.collection().find_one_and_replace(*args, **kwargs)

    @classmethod
    def find_one_and_delete(cls, *args, **kwargs):
        """Proxy for pymongo 'find_one_and_delete' method."""

        return cls.collection().find_one_and_delete(*args, **kwargs)

    def update(self, *args, **kwargs):
        """Proxy for dict 'update' method."""

        super(Document, self).update(*args, **kwargs)

    @classmethod
    def update_one(cls, *args, **kwargs):
        """Proxy for pymongo 'update_one' method."""

        return cls.collection().update_one(*args, **kwargs)

    @classmethod
    def update_many(cls, *args, **kwargs):
        """Proxy for pymongo 'update_many' method."""

        return cls.collection().update_many(*args, **kwargs)

    @classmethod
    def replace_one(cls, *args, **kwargs):
        """Proxy for pymongo 'replace_one' method."""

        return cls.collection().replace_one(*args, **kwargs)

    @classmethod
    def delete_one(cls, *args, **kwargs):
        """Proxy for pymongo 'delete_one' method."""

        return cls.collection().delete_one(*args, **kwargs)

    @classmethod
    def delete_many(cls, *args, **kwargs):
        """Proxy for pymongo 'delete_many' method."""

        return cls.collection().delete_many(*args, **kwargs)

    def insert(self, duplicate_error=None):
        """Inserts an instance of Document into collection.

        :returns: document '_id' field value
        """

        try:
            result = self.collection().insert_one(self.to_dict()).inserted_id
        except pymongo.errors.DuplicateKeyError:
            if duplicate_error is not None:
                raise duplicate_error
            else:
                raise

        if not self.get("_id"):
            self["_id"] = result

        return result

    def _get_query_dict(self, add_query=None):
        """Generates a query dict.

        Attention: method for internal use only!
        """

        query = {self.primary_key: self.id}
        query.update(add_query or {})

        return query

    def delete(self):
        """Deletes document from collection."""

        self.collection().delete_one(self._get_query_dict())

    @staticmethod
    def _check_write_status(write_result, upsert=False):
        """Check if write to primary was successfull."""

        if isinstance(write_result, WTimeoutError):
            return True

        if isinstance(write_result, OperationFailure):
            return False

        if not isinstance(write_result, dict):
            return False

        check_field = "nUpserted" if upsert else "nModified"

        return write_result.get(check_field, 0) > 0

    @staticmethod
    def _get_update_object(obj, fields):
        """
        Returns MongoDB update object for updating the specified document fields in
        the database.
        """

        to_set = {}
        to_unset = {}
        update_object = {}

        for field in fields:
            upper_field = ".".join(field.split(".")[:-1])

            while upper_field:
                if upper_field in fields:
                    break

                upper_field = ".".join(upper_field.split(".")[:-1])
            else:
                try:
                    value = obj
                    for name in field.split("."):
                        value = value[name]

                    to_set[field] = value
                except KeyError:
                    to_unset[field] = True

        if to_set:
            update_object.update({"$set": to_set})
        if to_unset:
            update_object.update({"$unset": to_unset})

        return update_object

    @classmethod
    def _save_object(cls, collection, query, obj):
        """Saves the specified document to the database."""

        try:
            result = collection.update(query, obj)
        except WTimeoutError as e:
            result = e

        return cls._check_write_status(result)

    @classmethod
    def _save_object_fields(cls, collection, query, obj, fields=None):
        """Saves the specified document fields to the database."""

        update = cls._get_update_object(obj, fields)
        if fields and update:
            return cls._save_object(collection, query, update)
        else:
            return True


    def commit_changes(self, fields=None, add_query=None):
        """Commits document changes to database.


        :param fields: string or iterable of document field(s) to commit
        :param add_query: optional query
        """

        query = self._get_query_dict()
        query.update(add_query or {})

        if not fields:
            return self._save_object(self.collection(), query, self.to_dict())
        else:
            return self._save_object_fields(
                self.collection(), query, self.to_dict(), fields)

    def pull_changes(self, fields=None, add_query=None):
        """Updates document fields with changes from database.

        Applying partial update if fields param specified

        :param fields: string or iterable of document field(s) to update
        :param add_query: optional query
        """

        query = self._get_query_dict()
        query.update(add_query or {})

        db_document = self.collection().find_one(query, projection=fields)
        if not db_document:
            raise self.NotFound(self.id)

        if not fields:
            fields = set(list(db_document) + list(self))

        db_document = MongoObject(db_document)

        for field in fields:
            try:
                db_document[field]
            except KeyError:
                try:
                    self[field]
                except KeyError:
                    pass
                else:
                    del self[field]
            else:
                self[field] = db_document[field]
