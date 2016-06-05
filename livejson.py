"""
A module implementing a pseudo-dict class which is bound to a JSON file. As you
change the contents of the dict, the JSON file will be updated in real-time.
"""

import collections
import os
import json


class _GenericDatabase(object):
    """ Class inherited by DictDatabase that implements all the required
    methods common between collections.MutableMapping and
    collections.MutableSequence in a way appropriate for JSON file-writing """
    @property
    def data(self):
        """ Get a vanilla dict object (fresh from the JSON file) """
        with open(self.path, "r") as f:
            return json.load(f)

    def __getitem__(self, key):
        return self.data[key]

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

    def __len__(self):
        return len(self.data)

    # Non-required methods

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return repr(self.data)


class DictDatabase(_GenericDatabase, collections.MutableMapping):
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


class ListDatabase(_GenericDatabase, collections.MutableSequence):
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
