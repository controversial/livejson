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
        my_db = livejson.Database(self.dbpath)
        my_db.cleardata()
        # Test nested dicts
        my_db["stored_data"] = {}
        my_db["stored_data"]["test"] = "value"
        self.assertEqual(my_db.data, {"stored_data": {"test": "value"}})
        # Test nested lists
        my_db["stored_data"] = []
        my_db["stored_data"].append("test")
        self.assertEqual(my_db.data, {"stored_data": ["test"]})
        # Test more complex multilevel nesting
        my_db["stored_data"] = []
        my_db["stored_data"].append({})
        my_db["stored_data"][0]["colors"] = ["green", "purple"]
        self.assertEqual(my_db.data,
                         {"stored_data": [{"colors": ["green", "purple"]}]}
                         )

    def tearDown(self):
        os.remove(self.dbpath)

if __name__ == "__main__":
    unittest.main()
