import os
import unittest

import livejson


class testDatabase(unittest.TestCase):
    """ Test the magical JSON database class """
    def setUp(self):
        # Path to JSON file
        self.dbpath = "test_database.json"

    def test_dict_database(self):
        """ Test that databases in which the base object is a dict work """
        # Test that a blank database can be properly created
        db = livejson.Database(self.dbpath)
        self.assertTrue(os.path.exists(self.dbpath))
        with open(self.dbpath, "r") as f:
            self.assertEqual(f.read(), "{}")

        # Test writing to a database
        db["a"] = "b"

        # Test reading values from an existing database
        newInstance = livejson.Database(self.dbpath).data
        self.assertEqual(newInstance["a"], "b")

        # Test the methods inherited from collections.MutableMapping
        # Test 'get'
        self.assertEqual(db.get("a"), "b")
        self.assertIsNone(db.get("penguins"))
        self.assertEqual(db.get("penguins", "fallback"), "fallback")
        # Test '__contains__'
        self.assertIn("a", db)
        # Test '__eq__'
        self.assertEqual(db, {"a": "b"})

        # Test the extra API I added
        # Test 'data' (get a vanilla dict object)
        self.assertEqual(db.data, {"a": "b"})

    def test_list_database(self):
        """ Test that databases in which the base object is an array work """
        # Create the database. Automatically, a blank database has a dict at
        # the base. So we write "[]" into the file manually so that livejson
        # detects the databse as a ListDatabase
        with open(self.dbpath, "w") as f:
            f.write("[]")
        db = livejson.Database(self.dbpath)
        # Test append, extend, and insert
        db.append("dogs")
        db.extend(["cats", "penguins"])
        db.insert(0, "turtles")
        self.assertIsInstance(db.data, list)
        self.assertEqual(db.data, ["turtles", "dogs", "cats", "penguins"])

    def test_nesting(self):
        """ Test that you can also work with dicts and lists that appear inside
        the database, rather than as the top-level object """
        db = livejson.Database(self.dbpath)
        db.cleardata()
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

    def test_switchclass(self):
        """ Test that it can automatically switch classes """
        # Test switching under normal usage
        db = livejson.Database(self.dbpath)
        assert isinstance(db, livejson.DictDatabase)
        db.setdata([])
        assert isinstance(db, livejson.ListDatabase)
        # Test switching when the database is manually changed
        with open(self.dbpath, "w") as f:
            f.write("{}")
        # This shouldn't error, it should change types when you do this
        db["dogs"] = "cats"
        self.assertIsInstance(db, livejson.DictDatabase)

    def tearDown(self):
        """ Called after _each test_ to remove the database """
        os.remove(self.dbpath)

if __name__ == "__main__":
    unittest.main()
