"""
A module implementing a pseudo-dict class which is bound to a JSON file. As you
change the contents of the dict, the JSON file will be updated in real-time.
"""

import collections
import os
import json


class Database(collections.MutableMapping):
    """ A class emulating a dict that is bound to a JSON file so that as the
    in-memory object is changed, the file is updated in real-time.

    Note that this class is significantly slower than a dict because every
    modification requires IO """
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

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)
