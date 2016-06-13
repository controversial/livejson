import os
import unittest

import livejson


class _DatabaseTest():
    dbpath = "test_database.json"

    def tearDown(self):
        """ Called after each test to remove the database """
        if os.path.exists(self.dbpath):
            os.remove(self.dbpath)



class TestDatabase(_DatabaseTest, unittest.TestCase):
    """ Test the magical JSON database class """
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

    def test_list_database(self):
        """ Test that databases in which the base object is an array work """
        # Create the database.
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

    def test_special_stuff(self):
        """ Test all the not-strictly-necessary extra API that I added """
        db = livejson.Database(self.dbpath)
        db["a"] = "b"
        # Test 'data' (get a vanilla dict object)
        self.assertEqual(db.data, {"a": "b"})
        # Test file_contents
        self.assertEqual(db.file_contents, "{\"a\": \"b\"}")
        # Test __str__ and __repr__
        self.assertEqual(str(db), str(db.data))
        self.assertEqual(repr(db), repr(db.data))
        # Test __iter__
        self.assertEqual(list(db), list(db.keys()))
        # Test clear_data
        db.clear_data()
        self.assertEqual(len(db.data), 0)
        # Test remove()
        db.remove()
        self.assertFalse(os.path.exists(self.dbpath))

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

    def test_staticmethod_initalization(self):
        """ Test initializing the Database in special ways with custom
        staticmethods """
        db = livejson.Database.with_data(self.dbpath, ["a", "b", "c"])
        self.assertEqual(db.data, ["a", "b", "c"])
        # Test initialization from JSON string
        os.remove(self.dbpath)
        db2 = livejson.Database.with_data(self.dbpath, "[\"a\", \"b\", \"c\"]")
        self.assertEqual(len(db2), 3)

    def test_errors(self):
        """ Test the errors that are set up """
        db = livejson.Database(self.dbpath)

        # Test error for trying to initialize in non-existant directories
        self.assertRaises(IOError, livejson.Database, "a/b/c.py")
        # Test error when trying to store non-string keys
        with self.assertRaises(TypeError):
            db[True] = "test"
        # Test that storing numeric keys raises a more helpful error message
        with self.assertRaisesRegexp(TypeError, "Try using a"):
            db[0] = "abc"
        # When initializing using with_data, test that an error is thrown if
        # the file already exists
        with self.assertRaises(ValueError):
            livejson.Database.with_data(self.dbpath, {})

    def test_empty_file(self):
        """ Test that a Database can be initialized in a completely empty, but
        existing, file """
        # Dict databases
        with open(self.dbpath, "w") as f:
            f.write("")
        db = livejson.Database(self.dbpath)
        self.assertEqual(db.data, {})
        # List databases
        with open(self.dbpath, "w") as f:
            f.write("")
        db = livejson.ListDatabase(self.dbpath)
        self.assertEqual(db.data, [])

    def test_rollback(self):
        """ Test that data can be restored in the case of an error to prevent
        corruption (see #3)"""
        class Test (object):
            pass
        db = livejson.Database(self.dbpath)
        db["a"] = "b"
        with self.assertRaises(TypeError):
            db["test"] = Test()
        self.assertEqual(db.data, {"a": "b"})


class TestNesting(_DatabaseTest, unittest.TestCase):
    def test_list_nesting(self):
        """ Test the nesting of lists inside a livejson.Database """
        db = livejson.Database(self.dbpath)
        db["stored_data"] = {}
        db["stored_data"]["test"] = "value"
        self.assertEqual(db.data, {"stored_data": {"test": "value"}})

    def test_dict_nesting(self):
        """ Test the nesting of dicts inside a livejson.Database """
        db = livejson.Database(self.dbpath)
        db["stored_data"] = []
        db["stored_data"].append("test")
        self.assertEqual(db.data, {"stored_data": ["test"]})

    def test_multilevel_nesting(self):
        """ Test that you can nest stuff inside nested stuff :O """
        db = livejson.Database(self.dbpath)
        db["stored_data"] = []
        db["stored_data"].append({})
        db["stored_data"][0]["colors"] = ["green", "purple"]
        self.assertEqual(db.data,
                         {"stored_data": [{"colors": ["green", "purple"]}]}
                         )

    def test_misc_methods(self):
        db = livejson.Database(self.dbpath)
        db["stored_data"] = [{"colors": ["green"]}]
        # Test that normal __getitem__ still works
        self.assertEqual(db["stored_data"][0]["colors"][0], "green")
        # Test deleting values
        db["stored_data"][0]["colors"].pop(0)
        self.assertEqual(len(db["stored_data"][0]["colors"]), 0)
        # Test __iter__ on nested dict
        db["stored_data"] = {"a": "b", "c": "d"}
        self.assertEqual(list(db["stored_data"]),
                         list(db["stored_data"].keys()))

    def test_errors(self):
        """ Test the errors that are thrown """
        db = livejson.Database(self.dbpath)
        db["data"] = {}
        # Test that storing non-string keys in a nested dict throws an error
        with self.assertRaises(TypeError):
            db["data"][True] = "test"
        # Test that storing numeric keys raises an additional error message
        with self.assertRaisesRegexp(TypeError, "Try using a"):
            db["data"][0] = "abc"


class TestGroupedWrites(_DatabaseTest, unittest.TestCase):
    """ Test using "grouped writes" with the context manager. These improve
    efficiency by only writing to the file once, at the end, instead of
    writing every change as it is made. """
    def test_basics(self):
        db = livejson.Database(self.dbpath)
        with db:
            db["a"] = "b"
            # Make sure that the write doesn't happen until we exit
            self.assertEqual(db.file_contents, "{}")
        self.assertEqual(db.file_contents, "{\"a\": \"b\"}")

    def test_lists(self):
        db = livejson.ListDatabase(self.dbpath)
        for i in range(10):
            db.append(i)
        self.assertEqual(len(db), 10)

    def test_switchclass(self):
        """ Test the switching of classes in the middle of a grouped write """
        db = livejson.Database(self.dbpath)
        with db:
            self.assertIsInstance(db, livejson.DictDatabase)
            db.set_data([])
            self.assertIsInstance(db, livejson.ListDatabase)
            self.assertEqual(db.file_contents, "{}")
        self.assertEqual(db.file_contents, "[]")

    def test_misc(self):
        """ Test miscellaneous other things that seem like they might break
        with a grouped write """
        db = livejson.Database(self.dbpath)
        # Test is_caching, and test that data works with the cache
        self.assertEqual(db.is_caching, False)
        with db:
            self.assertEqual(db.is_caching, True)
            db["a"] = "b"
            # Test that data reflects the cache
            self.assertEqual(db.data, {"a": "b"})
        self.assertEqual(db.is_caching, False)

    def test_fun_syntax(self):
        """ This is a fun bit of "syntactic sugar" enabled as a side effect of
        grouped writes. I also aliased "File" to "Database" to improve
        readability in some cases. """
        with livejson.File(self.dbpath) as a:
            a["cats"] = "dogs"
        with open(self.dbpath, "r") as f:
            self.assertEqual(f.read(), "{\"cats\": \"dogs\"}")


class TestAliases(_DatabaseTest, unittest.TestCase):
    def test_File(self):
        f = livejson.File(self.dbpath)
        self.assertTrue(os.path.exists(self.dbpath))
        self.assertEqual(f.data, {})

    def test_ListFile(self):
        f = livejson.ListFile(self.dbpath)
        self.assertTrue(os.path.exists(self.dbpath))
        self.assertEqual(f.data, [])

    def test_DictFile(self):
        f = livejson.DictFile(self.dbpath)
        self.assertTrue(os.path.exists(self.dbpath))
        self.assertEqual(f.data, {})


if __name__ == "__main__":
    unittest.main()
