import os
import unittest

import livejson


class testDatabase(unittest.TestCase):
    """ Test the magical JSON database class """
    dbpath = "test_database.json"

    def test_dict_database(self):
        """ Test that databases in which the base object is a dict work. This
        also tests all the shared methods"""
        # Test that a blank database can be properly created
        db = livejson.Database(self.dbpath)  # Test DictDatabase is default
        self.assertTrue(os.path.exists(self.dbpath))
        with open(self.dbpath, "r") as f:
            self.assertEqual(f.read(), "{}")
        # Test writing to a database
        db["a"] = "b"
        # Test reading values from an existing database
        newInstance = livejson.DictDatabase(self.dbpath).data  # Test explicit
        self.assertEqual(newInstance["a"], "b")
        # Test deleting values
        db["c"] = "d"
        self.assertIn("c", db)  # This also conviently tests __contains__
        del db["c"]
        self.assertNotIn("c", db)
        # Test error for raising in extra directories
        self.assertRaises(IOError, livejson.Database, "a/b/c.py")
        # Test the extra API I added
        # Test 'data' (get a vanilla dict object)
        self.assertEqual(db.data, {"a": "b"})
        # Test __str__ and __repr__
        self.assertEqual(str(db), str(db.data))
        self.assertEqual(repr(db), repr(db.data))
        # Test __iter__
        self.assertEqual(list(db), list(db.keys()))
        # Test remove()
        db.remove()
        self.assertFalse(os.path.exists(self.dbpath))

    def test_list_database(self):
        """ Test that databases in which the base object is an array work """
        # Create the database. Automatically, a blank database has a dict at
        # the base. So we write "[]" into the file manually so that livejson
        # detects the databse as a ListDatabase
        db = livejson.ListDatabase(self.dbpath)
        self.assertEqual(db.data, [])
        # Test append, extend, and insert
        db.append("dogs")
        db.extend(["cats", "penguins"])
        db.insert(0, "turtles")
        self.assertIsInstance(db.data, list)
        self.assertEqual(db.data, ["turtles", "dogs", "cats", "penguins"])
        # Test clear_data
        db.clear_data()
        self.assertEqual(len(db), 0)
        # Test creating a new ListDatabase automatically when file is an Array
        db2 = livejson.Database(self.dbpath)
        self.assertIsInstance(db2, livejson.ListDatabase)

    def test_nesting(self):
        """ Test that you can also work with dicts and lists that appear inside
        the database, rather than as the top-level object """
        db = livejson.Database(self.dbpath)
        db.clear_data()
        # Test nested dicts
        db["stored_data"] = {}
        db["stored_data"]["test"] = "value"
        self.assertEqual(db.data, {"stored_data": {"test": "value"}})
        # Test nested lists
        db["stored_data"] = []
        db["stored_data"].append("test")
        self.assertEqual(db.data, {"stored_data": ["test"]})
        # Test more complex multilevel nesting
        db["stored_data"] = []
        db["stored_data"].append({})
        db["stored_data"][0]["colors"] = ["green", "purple"]
        self.assertEqual(db.data,
                         {"stored_data": [{"colors": ["green", "purple"]}]}
                         )
        # Test that the old __getitem__ still works
        self.assertEqual(db["stored_data"][0]["colors"][0], "green")
        # Test deleting values
        db["stored_data"].pop(0)
        self.assertEqual(len(db["stored_data"]), 0)
        # Test __iter__ on nested dict
        db["stored_data"] = {"a": "b", "c": "d"}
        self.assertEqual(list(db["stored_data"]),
                         list(db["stored_data"].keys()))

    def test_switchclass(self):
        """ Test that it can automatically switch classes """
        # Test switching under normal usage
        db = livejson.Database(self.dbpath)
        self.assertIsInstance(db, livejson.DictDatabase)
        db.set_data([])
        self.assertIsInstance(db, livejson.ListDatabase)
        # Test switching when the database is manually changed
        with open(self.dbpath, "w") as f:
            f.write("{}")
        # This shouldn't error, it should change types when you do this
        db["dogs"] = "cats"
        self.assertIsInstance(db, livejson.DictDatabase)

    def test_with_data(self):
        db = livejson.Database.with_data(self.dbpath, ["a", "b", "c"])
        self.assertEqual(db.data, ["a", "b", "c"])
        with self.assertRaises(ValueError):
            livejson.Database.with_data(self.dbpath, {})
        # Test initialization from JSON string
        os.remove(self.dbpath)
        db2 = livejson.Database.with_data(self.dbpath, "[\"a\", \"b\", \"c\"]")
        self.assertEqual(len(db2), 3)

    def tearDown(self):
        """ Called after _each test_ to remove the database """
        if os.path.exists(self.dbpath):
            os.remove(self.dbpath)

if __name__ == "__main__":
    unittest.main()
