import os
import unittest

import livejson


class _BaseTest():
    path = "test_file.json"

    def tearDown(self):
        """ Called after each test to remove the file """
        if os.path.exists(self.path):
            os.remove(self.path)


class TestFile(_BaseTest, unittest.TestCase):
    """ Test the magical JSON file class """

    def test_DictFile(self):
        """ Test that 'livejson.File's in which the base object is a dict work
        as expected. This also tests all the methods shared between both types.
        """
        # Test that a blank JSON file can be properly created
        f = livejson.File(self.path)
        self.assertIsInstance(f, livejson.DictFile)  # Test DictFile is default
        self.assertTrue(os.path.exists(self.path))
        with open(self.path) as fi:
            self.assertEqual(fi.read(), "{}")
        # Test writing to a file
        f["a"] = "b"
        # Test reading values from an existing file
        newInstance = livejson.DictFile(self.path).data  # Tests explicit type
        self.assertEqual(newInstance["a"], "b")
        # Test deleting values
        f["c"] = "d"
        self.assertIn("c", f)  # This also conviently tests __contains__
        del f["c"]
        self.assertNotIn("c", f)

    def test_ListFile(self):
        """ Test that Files in which the base object is an array work """
        # Create the JSON file.
        f = livejson.ListFile(self.path)
        self.assertEqual(f.data, [])
        # Test append, extend, and insert
        f.append("dogs")
        f.extend(["cats", "penguins"])
        f.insert(0, "turtles")
        self.assertIsInstance(f.data, list)
        self.assertEqual(f.data, ["turtles", "dogs", "cats", "penguins"])
        # Test clear
        f.clear()
        self.assertEqual(len(f), 0)
        # Test creating a new ListFile automatically when file is an Array
        f2 = livejson.File(self.path)
        self.assertIsInstance(f2, livejson.ListFile)

    def test_special_stuff(self):
        """ Test all the not-strictly-necessary extra API that I added """
        f = livejson.File(self.path)
        f["a"] = "b"
        # Test 'data' (get a vanilla dict object)
        self.assertEqual(f.data, {"a": "b"})
        # Test file_contents
        self.assertEqual(f.file_contents, "{\"a\": \"b\"}")
        # Test __str__ and __repr__
        self.assertEqual(str(f), str(f.data))
        self.assertEqual(repr(f), repr(f.data))
        # Test __iter__
        self.assertEqual(list(f), list(f.keys()))
        # Test remove()
        f.remove()
        self.assertFalse(os.path.exists(self.path))

    def test_switchclass(self):
        """ Test that it can automatically switch classes """
        # Test switching under normal usage
        f = livejson.File(self.path)
        self.assertIsInstance(f, livejson.DictFile)
        f.set_data([])
        self.assertIsInstance(f, livejson.ListFile)
        # Test switching when the file is manually changed
        with open(self.path, "w") as fi:
            fi.write("{}")
        # This shouldn't error, it should change types when you do this
        f["dogs"] = "cats"
        self.assertIsInstance(f, livejson.DictFile)

    def test_staticmethod_initalization(self):
        """ Test initializing the File in special ways with custom
        staticmethods """
        f = livejson.File.with_data(self.path, ["a", "b", "c"])
        self.assertEqual(f.data, ["a", "b", "c"])
        # Test initialization from JSON string
        os.remove(self.path)
        f2 = livejson.File.with_data(self.path, "[\"a\", \"b\", \"c\"]")
        self.assertEqual(len(f2), 3)

    def test_errors(self):
        """ Test the errors that are set up """
        f = livejson.File(self.path)

        # Test error for trying to initialize in non-existant directories
        self.assertRaises(IOError, livejson.File, "a/b/c.py")
        # Test error when trying to store non-string keys
        with self.assertRaises(TypeError):
            f[True] = "test"
        # Test that storing numeric keys raises a more helpful error message
        with self.assertRaisesRegex(TypeError, "Try using a"):
            f[0] = "abc"
        # When initializing using with_data, test that an error is thrown if
        # the file already exists
        with self.assertRaises(ValueError):
            livejson.File.with_data(self.path, {})

    def test_empty_file(self):
        """ Test that a File can be initialized in a completely empty, but
        existing, file """
        # Dict files
        with open(self.path, "w") as fi:
            fi.write("")
        f = livejson.File(self.path)
        self.assertEqual(f.data, {})
        # List files
        with open(self.path, "w") as fi:
            fi.write("")
        f = livejson.ListFile(self.path)
        self.assertEqual(f.data, [])

    def test_rollback(self):
        """ Test that data can be restored in the case of an error to prevent
        corruption (see #3)"""
        class Test:
            pass
        f = livejson.File(self.path)
        f["a"] = "b"
        with self.assertRaises(TypeError):
            f["test"] = Test()
        self.assertEqual(f.data, {"a": "b"})

    def test_json_formatting(self):
        """ Test the extra JSON formatting options """
        # Test pretty formatting
        f = livejson.File(self.path, pretty=True)
        f["a"] = "b"
        self.assertEqual(f.file_contents, '{\n  "a": "b"\n}')
        f.indent = 4
        f.set_data(f.data)  # Force an update
        self.assertEqual(f.file_contents, '{\n    "a": "b"\n}')

        # Test sorting of keys
        f["b"] = "c"
        f["d"] = "e"
        f["c"] = "d"
        self.assertTrue(f.file_contents.find("a") <
                        f.file_contents.find("b") <
                        f.file_contents.find("c") <
                        f.file_contents.find("d")
                        )


class TestNesting(_BaseTest, unittest.TestCase):
    def test_list_nesting(self):
        """ Test the nesting of lists inside a livejson.File """
        f = livejson.File(self.path)
        f["stored_data"] = {}
        f["stored_data"]["test"] = "value"
        self.assertEqual(f.data, {"stored_data": {"test": "value"}})

    def test_dict_nesting(self):
        """ Test the nesting of dicts inside a livejson.File """
        f = livejson.File(self.path)
        f["stored_data"] = []
        f["stored_data"].append("test")
        self.assertEqual(f.data, {"stored_data": ["test"]})

    def test_multilevel_nesting(self):
        """ Test that you can nest stuff inside nested stuff :O """
        f = livejson.File(self.path)
        f["stored_data"] = []
        f["stored_data"].append({})
        f["stored_data"][0]["colors"] = ["green", "purple"]
        self.assertEqual(f.data,
                         {"stored_data": [{"colors": ["green", "purple"]}]}
                         )

    def test_misc_methods(self):
        f = livejson.File(self.path)
        f["stored_data"] = [{"colors": ["green"]}]
        # Test that normal __getitem__ still works
        self.assertEqual(f["stored_data"][0]["colors"][0], "green")
        # Test deleting values
        f["stored_data"][0]["colors"].pop(0)
        self.assertEqual(len(f["stored_data"][0]["colors"]), 0)
        # Test __iter__ on nested dict
        f["stored_data"] = {"a": "b", "c": "d"}
        self.assertEqual(list(f["stored_data"]),
                         list(f["stored_data"].keys()))

    def test_errors(self):
        """ Test the errors that are thrown """
        f = livejson.File(self.path)
        f["data"] = {}
        # Test that storing non-string keys in a nested dict throws an error
        with self.assertRaises(TypeError):
            f["data"][True] = "test"
        # Test that storing numeric keys raises an additional error message
        with self.assertRaisesRegex(TypeError, "Try using a"):
            f["data"][0] = "abc"


class TestGroupedWrites(_BaseTest, unittest.TestCase):
    """ Test using "grouped writes" with the context manager. These improve
    efficiency by only writing to the file once, at the end, instead of
    writing every change as it is made. """

    def test_basics(self):
        f = livejson.File(self.path)
        with f:
            f["a"] = "b"
            # Make sure that the write doesn't happen until we exit
            self.assertEqual(f.file_contents, "{}")
        self.assertEqual(f.file_contents, "{\"a\": \"b\"}")

    def test_with_existing_file(self):
        """ Test that the with block won't clear data """
        f = livejson.File(self.path)
        f["a"] = "b"
        with f:
            f["c"] = "d"
        self.assertIn("a", f)

    def test_lists(self):
        f = livejson.ListFile(self.path)
        with f:
            for i in range(10):
                f.append(i)
            self.assertEqual(f.file_contents, "[]")
        self.assertEqual(len(f), 10)

    def test_switchclass(self):
        """ Test the switching of classes in the middle of a grouped write """
        f = livejson.File(self.path)
        with f:
            self.assertIsInstance(f, livejson.DictFile)
            f.set_data([])
            self.assertIsInstance(f, livejson.ListFile)
            self.assertEqual(f.file_contents, "{}")
        self.assertEqual(f.file_contents, "[]")

    def test_misc(self):
        """ Test miscellaneous other things that seem like they might break
        with a grouped write """
        f = livejson.File(self.path)
        # Test is_caching, and test that data works with the cache
        self.assertEqual(f.is_caching, False)
        with f:
            self.assertEqual(f.is_caching, True)
            f["a"] = "b"
            # Test that data reflects the cache
            self.assertEqual(f.data, {"a": "b"})
        self.assertEqual(f.is_caching, False)

    def test_fun_syntax(self):
        """ This is a fun bit of "syntactic sugar" enabled as a side effect of
        grouped writes. """
        with livejson.File(self.path) as f:
            f["cats"] = "dogs"
        with open(self.path) as fi:
            self.assertEqual(fi.read(), "{\"cats\": \"dogs\"}")


class TestAliases(_BaseTest, unittest.TestCase):
    def test_Database(self):
        db = livejson.Database(self.path)
        self.assertTrue(os.path.exists(self.path))
        self.assertEqual(db.data, {})

    def test_ListDatabase(self):
        db = livejson.ListDatabase(self.path)
        self.assertTrue(os.path.exists(self.path))
        self.assertEqual(db.data, [])

    def test_DictDatabase(self):
        db = livejson.DictDatabase(self.path)
        self.assertTrue(os.path.exists(self.path))
        self.assertEqual(db.data, {})


if __name__ == "__main__":
    unittest.main()
