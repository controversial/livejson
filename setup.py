from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name="livejson",
    py_modules=["livejson"],
    version="1.9.1",
    description="Bind Python objects to JSON files",
    long_description=readme,
    long_description_content_type="text/markdown",
    keywords="livejson json io development file files live update",
    license="MIT",
    author="Luke Taylor",
    author_email="luke@deentaylor.com",
    url="https://github.com/controversial/livejson/",
)
