# `livejson`
A Python library implementing a `dict`-like object that writes to a file as it is modified

Thanks to [dgelessus](https://github.com/dgelessus) for naming this project.

## Installing
`livejson` supports both Python 2 and 3, and can be easily installed with `pip`.
```bash
# Python 2
sudo pip install livejson
# Python 3
sudo pip3 install livejson
```
After installing, you can just `import livejson` from your code!

## Example usage
```python
>>> import livejson
>>> my_db = livejson.Database("test.json")
>>> my_db['dogs'] = "cats"
>>> with open("test.json", "r") as f:
...     print(f.read())
...
{"dogs": "cats"}
>>> my_db['dogs']
'cats'
```

## Notes
This class does not currently support nesting. What this means is that something like this:
```python
import livejson
my_db = livejson.Database("test.json")
my_db['data'] = {}
my_db['data']['dogs'] = 'cats'
```
will not work as expected; `my_db['data']` will still be `{}`. However, this is planned for the future by converting all dicts and lists passed to `__setitem__` to special subclasses that will automatically handle writing when *they* are modified.
