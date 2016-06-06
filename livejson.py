"""
A module implementing a pseudo-dict class which is bound to a JSON file. As you
change the contents of the dict, the JSON file will be updated in real-time.
"""

import collections
import os
import json


# MISC HELPERS


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
            nestClass = _NestedList if isinstance(out, list) else _NestedBase
            return nestClass(toplevel, newPathInData)
        # Not a list or a dict, don't worry about it
        else:
            return out

    def __len__(self):
        return len(self.data)

    # Non-required methods

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return repr(self.data)


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
        self.basedb.setdata(data)

    def __delitem__(self, key):
        # See __setitem__ for details on how this works
        data = self.basedb.data
        d = data
        for i in self.pathInData:
            d = d[i]
        del d[key]
        self.basedb.setdata(data)


class _NestedDict(_NestedBase, collections.MutableMapping):
    def __iter__(self):
        return iter(self.data)


class _NestedList(_NestedBase, collections.MutableSequence):
    def insert(self, index, value):
        # See _NestedBase.__setitem__ for details on how this works
        data = self.basedb.data
        d = data
        for i in self.pathInData:
            d = d[i]
        d.insert(index, value)
        self.basedb.setdata(data)


# THE MAIN CLASSES


class _BaseDatabase(_ObjectBase):
    """ Class inherited by DictDatabase that implements all the required
    methods common between collections.MutableMapping and
    collections.MutableSequence in a way appropriate for JSON file-writing """
    @property
    def data(self):
        """ Get a vanilla dict object (fresh from the JSON file) """
        # Update type in case it's changed
        self._updateType()
        with open(self.path, "r") as f:
            return json.load(f)

    def __setitem__(self, key, value):
        data = self.data
        data[key] = value
        with open(self.path, "w") as f:
            json.dump(data, f)

    def __delitem__(self, key):
        data = self.data
        del data[key]
        with open(self.path, "w") as f:
            json.dump(data, f)

    def _updateType(self):
        """ Make sure that the class behaves like the data structure that it
        is, so that we don't get a ListDatabase trying to represent a dict"""
        # Do this manually to avoid infinite recursion
        with open(self.path, "r") as f:
            data = json.load(f)
        # Change type if needed
        if isinstance(data, dict) and isinstance(self, ListDatabase):
            self.__class__ = DictDatabase
        elif isinstance(data, list) and isinstance(self, DictDatabase):
            self.__class__ = ListDatabase
    # Bonus features!

    def setdata(self, data):
        """ Overwrite the database with new data. You probably shouldn't do
        this yourself, it's easy to screw up your whole database with this """
        with open(self.path, "w") as f:
            json.dump(data, f)
        self._updateType()


class DictDatabase(_BaseDatabase, collections.MutableMapping):
    """ A class emulating Python's dict that will update a JSON file as it is
    modified """
    def __init__(self, path):
        self.path = path

        # The database will need to be created if it doesn't exist
        if not os.path.exists(self.path):
            # Raise exception if the directory that should contain the file
            # doesn't exist
            dirname = os.path.dirname(self.path)
            if dirname and not os.path.exists(dirname):
                raise IOError(
                    ("Could not initialize empty database in non-existant "
                     "directory '{}'").format(os.path.dirname(self.path))
                )
            # Write an empty database there
            with open(self.path, "w") as f:
                f.write("{}")

    def __iter__(self):
        return iter(self.data)

    def cleardata(self):
        """ Delete everything. Dangerous. """
        self.setdata({})


class ListDatabase(_BaseDatabase, collections.MutableSequence):
    """ A class emulating a Python list that will update a JSON file as it is
    modified. Use this class directly when creating a new database if you want
    the base object to be an array. """
    def __init__(self, path):
        self.path = path

        # The database will need to be created if it doesn't exist
        if not os.path.exists(self.path):
            # Raise exception if the directory that should contain the file
            # doesn't exist
            dirname = os.path.dirname(self.path)
            if dirname and not os.path.exists(dirname):
                raise IOError(
                    ("Could not initialize empty list database in non-existant"
                     " directory '{}'").format(os.path.dirname(self.path))
                )
            # Write an empty database there
            with open(self.path, "w") as f:
                f.write("[]")

    def insert(self, index, value):
        data = self.data
        data.insert(index, value)
        with open(self.path, "w") as f:
            json.dump(data, f)

    def cleardata(self):
        """ Delete everything. Dangerous. """
        self.setdata([])


def Database(path):
    """ An emulation of a Python object, bound to a JSON file so that as
    the in-memory object is changed, the file is updated in real-time.

    This isn't actually a class, but it returns one, so you can use it as if it
    was one.

    Note that this class is significantly slower than a dict because every
    modification requires IO """

    # When creating a blank database, it's better to make the top-level an
    # Object, rather than an Array, because that's the case in most JSON files.
    if not os.path.exists(path):
        return DictDatabase(path)
    else:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return DictDatabase(path)
        elif isinstance(data, list):
            return ListDatabase(path)
