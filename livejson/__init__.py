"""A module implementing a pseudo-dict class which is bound to a JSON file.

As you change the contents of the dict, the JSON file will be updated in
real-time. Magic.
"""

from __future__ import annotations

import enum
import json
import os
from collections.abc import MutableMapping, MutableSequence
from enum import Enum
from typing import Union, Any

PathLike = Union[str, os.PathLike]


# MISC HELPERS


class _DataType(Enum):
    List = enum.auto()
    Dict = enum.auto()


def _initfile(path: PathLike, data_type: _DataType = _DataType.Dict) -> bool | None:  # TODO: is return really neccessary? Not used anywhere
    """Initialize an empty JSON file."""
    data: dict[Any, Any] | list[Any] = {} if data_type is _DataType.Dict else []
    # The file will need to be created if it doesn't exist
    if not os.path.exists(path):  # The file doesn't exist
        # Raise exception if the directory that should contain the file doesn't
        # exist
        dirname = os.path.dirname(path)
        if dirname and not os.path.exists(dirname):
            raise IOError(  # TODO: better error (IOError is deprecated)
                ("Could not initialize empty JSON file in non-existant "
                 "directory '{}'").format(os.path.dirname(path))
            )
        # Write an empty file there
        with open(path, "w") as f:
            json.dump(data, f)
        return True
    elif os.path.getsize(path) == 0:  # The file is empty
        with open(path, "w") as f:
            json.dump(data, f)
    else:  # The file exists and contains content
        return False


class _ObjectBase:
    """Class inherited by most things.

    Implements the lowest common denominator for all emulating classes.
    """

    def __getitem__(self, key):
        out = self.data[key]

        # Nesting
        if isinstance(out, (list, dict)):
            # If it's the top level, we can use [] for the path
            pathInData = self.pathInData if hasattr(self, "pathInData") else []
            newPathInData = pathInData + [key]
            # The top level, i.e. the File class, not a nested class. If we're
            # already the top level, just use self.
            toplevel = self.base if hasattr(self, "base") else self
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
        """Make sure the type of a key is appropriate."""
        pass


# NESTING CLASSES


class _NestedBase(_ObjectBase):
    """Inherited by _NestedDict and _NestedList, implements methods common
    between them. Takes arguments 'fileobj' which specifies the parent File
    object, and 'pathToThis' which specifies where in the JSON file this object
    exists (as a list).
    """

    def __init__(self, fileobj, pathToThis):
        self.pathInData = pathToThis
        self.base = fileobj

    @property
    def data(self):
        # Start with the top-level data
        d = self.base.data
        # Navigate through the object to find where self.pathInData points
        for i in self.pathInData:
            d = d[i]
        # And return the result
        return d

    def __setitem__(self, key, value):
        self._checkType(key)
        # Store the whole data
        data = self.base.data
        # Iterate through and find the right part of the data
        d = data
        for i in self.pathInData:
            d = d[i]
        # It is passed by reference, so modifying the found object modifies
        # the whole thing
        d[key] = value
        # Update the whole file with the modification
        self.base.data = data

    def __delitem__(self, key):
        # See __setitem__ for details on how this works
        data = self.base.data
        d = data
        for i in self.pathInData:
            d = d[i]
        del d[key]
        self.base.data = data


class _NestedDict(_NestedBase, MutableMapping):
    """A pseudo-dict class to replace vanilla dicts inside a livejson.File.

    This "watches" for changes made to its content, then tells
    the base livejson.File instance to update itself so that the file always
    reflects the changes you've made.

    This class is what allows for nested calls like this

    >>> f = livejson.File("myfile.json")
    >>> f["a"]["b"]["c"] = "d"

    to update the file.
    """

    def __iter__(self):
        return iter(self.data)

    def _checkType(self, key):
        if not isinstance(key, str):
            raise TypeError("JSON only supports strings for keys, not '{}'. {}"
                            .format(type(key).__name__, "Try using a list for"
                                    " storing numeric keys" if
                                    isinstance(key, int) else ""))


class _NestedList(_NestedBase, MutableSequence):
    """A pseudo-list class to replace vanilla lists inside a livejson.File.

    This "watches" for changes made to its content, then tells
    the base livejson.File instance to update itself so that the file always
    reflects the changes you've made.

    This class is what allows for nested calls involving lists like this:

    >>> f = livejson.File("myfile.json")
    >>> f["a"].append("foo")

    to update the file.
    """

    def insert(self, index, value):
        # See _NestedBase.__setitem__ for details on how this works
        data = self.base.data
        d = data
        for i in self.pathInData:
            d = d[i]
        d.insert(index, value)
        self.base.data = data


# THE MAIN INTERFACE


class _BaseFile(_ObjectBase):
    """Class inherited by DictFile and ListFile.

    This implements all the required methods common between
    MutableMapping and MutableSequence."""

    def __init__(self, path, pretty=False, sort_keys=False):
        self.path = path
        self.pretty = pretty
        self.sort_keys = sort_keys
        self.indent = 2  # Default indentation level

        _initfile(self.path,
                  _DataType.List if isinstance(self, ListFile) else _DataType.Dict)

    def _data(self):
        """A simpler version of data to avoid infinite recursion in some cases.

        Don't use this.
        """
        if self.is_caching:
            return self.cache
        with open(self.path) as f:
            return json.load(f)

    @property
    def data(self):
        """Get a vanilla dict object to represent the file."""
        # Update type in case it's changed
        self._updateType()
        # And return
        return self._data()

    @data.setter
    def data(self, data):
        """Overwrite the file with new data. You probably shouldn't do
        this yourself, it's easy to screw up your whole file with this."""
        if self.is_caching:
            self.cache = data
        else:
            fcontents = self.file_contents
            with open(self.path, "w") as f:
                try:
                    # Write the file. Keep user settings about indentation, etc
                    indent = self.indent if self.pretty else None
                    json.dump(data, f, sort_keys=self.sort_keys, indent=indent)
                except Exception as e:
                    # Rollback to prevent data loss
                    f.seek(0)
                    f.truncate()
                    f.write(fcontents)
                    # And re-raise the exception
                    raise e
        self._updateType()

    def __setitem__(self, key, value):
        self._checkType(key)
        data = self.data
        data[key] = value
        self.data = data

    def __delitem__(self, key):
        data = self.data
        del data[key]
        self.data = data

    def _updateType(self):
        """Make sure that the class behaves like the data structure that it
        is, so that we don't get a ListFile trying to represent a dict."""
        data = self._data()
        # Change type if needed
        if isinstance(data, dict) and isinstance(self, ListFile):
            self.__class__ = DictFile
        elif isinstance(data, list) and isinstance(self, DictFile):
            self.__class__ = ListFile

    # Bonus features!

    def remove(self):
        """Delete the file from the disk completely."""
        os.remove(self.path)

    @property
    def file_contents(self):
        """Get the raw file contents of the file."""
        with open(self.path) as f:
            return f.read()

    # Grouped writes

    @property
    def is_caching(self):
        """Returns a boolean value describing whether a grouped write is
        underway.
        """
        return hasattr(self, "cache")

    def __enter__(self):
        self.cache = self.data
        return self  # This enables using "as"

    def __exit__(self, *args):
        # We have to write manually here because __setitem__ is set up to write
        # to cache, not to file
        with open(self.path, "w") as f:
            # Write the file. Keep user settings about indentation, etc
            indent = self.indent if self.pretty else None
            json.dump(self.cache, f, sort_keys=self.sort_keys, indent=indent)
        del self.cache


class DictFile(_BaseFile, MutableMapping):
    """A class emulating Python's dict that will update a JSON file as it is
    modified.
    """

    def __iter__(self):
        return iter(self.data)

    def _checkType(self, key):
        if not isinstance(key, str):
            raise TypeError("JSON only supports strings for keys, not '{}'. {}"
                            .format(type(key).__name__, "Try using a list for"
                                    " storing numeric keys" if
                                    isinstance(key, int) else ""))


class ListFile(_BaseFile, MutableSequence):
    """A class emulating a Python list that will update a JSON file as it is
    modified. Use this class directly when creating a new file if you want the
    base object to be an array.
    """

    def insert(self, index, value):
        data = self.data
        data.insert(index, value)
        self.data = data

    def clear(self):
        # Under Python 3, this method is already in place. I've implemented it
        # myself to maximize compatibility with Python 2. Note that the
        # docstring here is stolen from Python 3.
        """L.clear() -> None -- remove all items from L."""
        self.data = []


class File:
    """The main interface of livejson. Emulates a list or a dict, updating a
    JSON file in real-time as it is modified.

    This will be automatically replaced with either a ListFile or as
    DictFile based on the contents of your file (a DictFile is the default when
    creating a new file).
    """

    def __init__(self, path, pretty=False, sort_keys=True, indent=2):
        # When creating a blank JSON file, it's better to make the top-level an
        # Object ("dict" in Python), rather than an Array ("list" in python),
        # because that's the case for most JSON files.
        self.path = path
        self.pretty = pretty
        self.sort_keys = sort_keys
        self.indent = indent

        _initfile(self.path)

        with open(self.path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            self.__class__ = DictFile
        elif isinstance(data, list):
            self.__class__ = ListFile

    @classmethod
    def with_data(cls, path, data, *args, **kwargs):
        """Initialize a new file that starts out with some data. Pass data
        as a list, dict, or JSON string.
        """
        # De-jsonize data if necessary
        if isinstance(data, str):
            data = json.loads(data)

        # Make sure this is really a new file
        if os.path.exists(path):
            raise ValueError("File exists, not overwriting data. Set the "
                             "'data' attribute on a normally-initialized "
                             "'livejson.File' instance if you really "
                             "want to do this.")
        else:
            f = cls(path, *args, **kwargs)
            f.data = data
            return f
