<h1 align="center">livejson</h1>

<p align="center">
    <a href="https://travis-ci.org/controversial/livejson" align="center">
        <img alt="Build Status" src="https://travis-ci.org/controversial/livejson.svg?branch=master">
    </a>
    <a href="https://coveralls.io/github/controversial/livejson?branch=master" align="center">
        <img alt="Coverage Status" src="https://coveralls.io/repos/github/controversial/livejson/badge.svg?branch=master">
    </a>
    <a href="https://www.python.org/dev/peps/pep-0008/" align="center">
        <img alt="PEP8" src="https://img.shields.io/badge/PEP8-compliant-brightgreen.svg">
    </a>
</p>

<p align="center">An interface to transparently bind Python objects to JSON files, so that all changes made to the object are reflected in the JSON file</p>

---


`livejson` allows you to cleanly manipulate JSON objects as though they were Python `dict`s, with your file transparently updating in the background. It's **pure-python with no dependencies**.

![Demo gif](https://i.imgur.com/yaXzzjG.gif)

`livejson` is:

- **Easy**: use `livejson` with the same interface as Python `list`s and `dict`s, meaning it can basically be used as a drop-in replacement.
- **Flexible**: `livejson` fully supports complex nestings of `list`s and `dict`s, meaning it can represent any valid JSON file.
- **Compatible**: `livejson` works on all [versions](https://devguide.python.org/versions/) of Python that are not end-of-life.
- **Lightweight**: `livejson` is a single file with no external dependencies. Just install and go!
- **Reliable**: by default, no caching is used. Every single time you access a `livejson.File`, it's read straight from the file. And every time you write to it, the change is instant. No delays, no conflicts. However, if efficiency is important, you can use the context manager to perform "grouped writes", which allow for performing a large number of operations with only one write at the end.
- **100% test covered** Be confident that `livejson` is working properly

`livejson` can be used for:

- **Database storage**: you can use `livejson` to easily write flexible JSON databases, without having to worry about complex `open` and `close` operations, or learning how to use the `json` module.
- **Debugging**: You can use `livejson` to “back up” your Python objects to disk. If you use a `livejson.File` instead of a `dict` or a `list` and your script crashes, you'll still have a hard copy of your object. And you barely had to change any of your code.
- **General-purpose JSON**: If your script or application needs to interact with JSON files in any way, consider using `livejson`, for simplicity's sake. `livejson` can make your code easier to read and understand, and also save you time.

Thanks to [dgelessus](https://github.com/dgelessus) for naming this project.

## Installing
`livejson` can be easily installed with `pip`.
```bash
pip install livejson
```
After installing, you can just `import livejson` from your code!

## Example usage
Basic usage:
```python
import livejson
f = livejson.File("test.json")
f["a"] = "b"
# That's it, the file has been written to!
```
As a context manager:
```python
import livejson
with livejson.File("test.json") as f:
    f["a"] = "b"
```
