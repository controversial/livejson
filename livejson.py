"""
A module implementing a pseudo-dict class which is bound to a JSON file. As you
change the contents of the dict, the JSON file will be updated in real-time.
"""

import collections
import os
import json


# MISC HELPERS


def _initdb(path, data="dict"):
    """ Initialize an empty database """
    data = {} if data.lower() == "dict" else []
    # The database will need to be created if it doesn't exist
    if not os.path.exists(path):  # The file doesn't exist
        # Raise exception if the directory that should contain the file doesn't
        # exist
        dirname = os.path.dirname(path)
        if dirname and not os.path.exists(dirname):
            raise IOError(
                ("Could not initialize empty database in non-existant "
                 "directory '{}'").format(os.path.dirname(path))
            )
        # Write an empty database there
        with open(path, "w") as f:
            json.dump(data, f)
        return True
    elif len(open(path, "r").read()) == 0:  # The file is empty
        with open(path, "w") as f:
            json.dump(data, f)
    else:  # The file exists and contains content
        return False


class _ObjectBase(object):
    """ Class inherited by most stuff. Implements the lowest common denominator
    for most stuff """
    def __getitem__(self, key):
        out = self.data[key]

        # Nesting
        if isinstance(out, (list, dict)):
            # If it's the top level database, we can use [] for the path
            pathInData = self.pathInData if hasattr(self, "pathInData") else []
            newPathInData = pathInData + [key]
            # If it's the top level database, use self for top level database
            toplevel = self.basedb if hasattr(self, "basedb") else self
            nestClass = _NestedList if isinstance(out, list) else _NestedDict
            return nestClass(toplevel, newPathInData)
        # Not a list or a dict, don't worry about it
        else:
            return out

    def __len__(self):
        return len(self.data)

    # Methods not-required by the ABC

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return repr(self.data)

    # MISC
    def _checkType(self, key):
        """ Make sure the type of a key is appropriate """
        pass

# NESTING CLASSES


class _NestedBase(_ObjectBase):
    """ Inherited by _NestedDict and _NestedList, implements methods common
    between them. Takes arguments 'db' which specifies the parent database, and
    'pathToThis' which specifies where in the database this object exists (as a
    list)."""
    def __init__(self, db, pathToThis):
        self.pathInData = pathToThis
        self.basedb = db

    @property
    def data(self):
        # Start with the top-level database data
        d = self.basedb.data
        # Navigate through the object to find where self.pathInData points
        for i in self.pathInData:
            d = d[i]
        # And return the result
        return d

    def __setitem__(self, key, value):
        self._checkType(key)
        # Store the whole data
        data = self.basedb.data
        # Iterate through and find the right part of the data
        d = data
        for i in self.pathInData:
            d = d[i]
        # It is passed by reference, so modifying the found object modifies
        # the whole thing
        d[key] = value
        # Update the whole database with the modification
        self.basedb.set_data(data)

    def __delitem__(self, key):
        # See __setitem__ for details on how this works
        data = self.basedb.data
        d = data
        for i in self.pathInData:
            d = d[i]
        del d[key]
        self.basedb.set_data(data)


class _NestedDict(_NestedBase, collections.MutableMapping):
    def __iter__(self):
        return iter(self.data)

    def _checkType(self, key):
        if not isinstance(key, str):
            raise TypeError("JSON only supports strings for keys, not '{}'. {}"
                            .format(type(key).__name__, "Try using a list for"
                                    " storing numeric keys" if
                                    isinstance(key, int) else ""))


class _NestedList(_NestedBase, collections.MutableSequence):
    def insert(self, index, value):
        # See _NestedBase.__setitem__ for details on how this works
        data = self.basedb.data
        d = data
        for i in self.pathInData:
            d = d[i]
        d.insert(index, value)
        self.basedb.set_data(data)


# THE MAIN CLASSES


class _BaseDatabase(_ObjectBase):
    """ Class inherited by DictDatabase that implements all the required
    methods common between collections.MutableMapping and
    collections.MutableSequence in a way appropriate for JSON file-writing """
    def __init__(self, path):
        self.path = path
        _initdb(self.path,
                "list" if isinstance(self, ListDatabase) else "dict")

    def _data(self):
        """ A simplified version of 'data' to avoid infinite recursion in some
        cases. Don't use this. """
        if self.is_caching:
            return self.cache
        with open(self.path, "r") as f:
            return json.load(f)

    @property
    def data(self):
        """ Get a vanilla dict object to represent the database """
        # Update type in case it's changed
        self._updateType()
        # And return
        return self._data()

    def __setitem__(self, key, value):
        self._checkType(key)
        data = self.data
        data[key] = value
        self.set_data(data)

    def __delitem__(self, key):
        data = self.data
        del data[key]
        self.set_data(data)

    def _updateType(self):
        """ Make sure that the class behaves like the data structure that it
        is, so that we don't get a ListDatabase trying to represent a dict """
        data = self._data()
        # Change type if needed
        if isinstance(data, dict) and isinstance(self, ListDatabase):
            self.__class__ = DictDatabase
        elif isinstance(data, list) and isinstance(self, DictDatabase):
            self.__class__ = ListDatabase

    # Bonus features!

    def set_data(self, data):
        """ Overwrite the database with new data. You probably shouldn't do
        this yourself, it's easy to screw up your whole database with this """
        if self.is_caching:
            self.cache = data
        else:
            fcontents = self.file_contents
            with open(self.path, "w") as f:
                try:
                    json.dump(data, f)
                except Exception as e:
                    # Rollback to prevent data loss
                    f.seek(0)
                    f.truncate()
                    f.write(fcontents)
                    # And re-raise the exception
                    raise e
        self._updateType()

    def remove(self):
        """ Delete the database from the disk completely """
        os.remove(self.path)

    @property
    def file_contents(self):
        """ Get the raw file contents of the database """
        with open(self.path, "r") as f:
            return f.read()

    # Grouped writes

    @property
    def is_caching(self):
        """ Is a grouped write underway? """
        return hasattr(self, "cache")

    def __enter__(self):
        self.cache = self.data
        return self  # This enables using "as"

    def __exit__(self, *args):
        # We have to write manually here because __setitem__ is set up to write
        # to cache, not to file
        with open(self.path, "w") as f:
            json.dump(self.cache, f)
        del self.cache


class DictDatabase(_BaseDatabase, collections.MutableMapping):
    """ A class emulating Python's dict that will update a JSON file as it is
    modified """
    def __iter__(self):
        return iter(self.data)

    def _checkType(self, key):
        if not isinstance(key, str):
            raise TypeError("JSON only supports strings for keys, not '{}'. {}"
                            .format(type(key).__name__, "Try using a list for"
                                    " storing numeric keys" if
                                    isinstance(key, int) else ""))


class ListDatabase(_BaseDatabase, collections.MutableSequence):
    """ A class emulating a Python list that will update a JSON file as it is
    modified. Use this class directly when creating a new database if you want
    the base object to be an array. """
    def insert(self, index, value):
        data = self.data
        data.insert(index, value)
        self.set_data(data)

    def clear(self):
        # Under Python 3, this method is already in place. I've implemented it
        # myself to maximize compatibility with Python 2. Note that the
        # docstring here is stolen from Python 3.
        """ L.clear() -> None -- remove all items from L """
        self.set_data([])


class Database(object):
    """ The main interface of livejson. Emulates a list or a dict, updating a
    JSON file in real-time as it is modified.

    This will be automatically replaced with either a ListDatabase or as
    DictDatabase based on the contents of your file (DictDatabase by default).
    """

    def __init__(self, path):
        # When creating a blank database, it's better to make the top-level an
        # Object ("dict" in Python), rather than an Array ("list" in python),
        # because that's the case for most JSON files.
        self.path = path
        _initdb(self.path)

        with open(self.path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            self.__class__ = DictDatabase
        elif isinstance(data, list):
            self.__class__ = ListDatabase

    @staticmethod
    def with_data(path, data):
        """ Initialize a new database that starts out with some data. Pass data
        as a list, dict, or JSON string. """
        # De-jsonize data if necessary
        if isinstance(data, str):
            data = json.loads(data)

        # Make sure this is really a new database
        if os.path.exists(path):
            raise ValueError("Database exists, not overwriting data. Use "
                             "'set_data' if you really want to do this.")
        else:
            db = Database(path)
            db.set_data(data)
            return db


# Aliases
File = Database
ListFile = ListDatabase
DictFile = DictDatabase
