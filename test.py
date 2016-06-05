import os
import unittest

import livejson


class testDatabase(unittest.TestCase):
    """ Test the magical JSON database class """
    def setUp(self):
        # Path to JSON file
        self.dbpath = "test_database.json"

    def test_database_main(self):
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

    def tearDown(self):
        os.remove(self.dbpath)

if __name__ == "__main__":
    unittest.main()
