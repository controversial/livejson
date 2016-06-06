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
Creating a new database:
```python
>>> import livejson
>>> my_db = livejson.Database("test.json")
>>> my_db["dogs"] = "cats"
>>> with open("test.json", "r") as f:
...     print(f.read())
...
{"dogs": "cats"}
>>> my_db["dogs"]
'cats'
```
Reading and modifying an existing database:
```python
>>> my_db = livejson.Database("test.json")
>>> my_db["dogs"]
u'cats'
>>> my_db["dogs"] = "fish"
>>> with open("test.json", "r") as f:
...     print(f.read())
...
{"dogs": "fish"}
>>>
```
