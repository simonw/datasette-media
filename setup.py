from setuptools import setup
import os

VERSION = "0.1a"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-media",
    description="Datasette plugin for serving media based on a SQL query",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-media",
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_media"],
    entry_points={"datasette": ["media = datasette_media"]},
    install_requires=["datasette>=0.42", "starlette"],
    extras_require={"test": ["pytest", "pytest-asyncio", "httpx"]},
    tests_require=["datasette-media[test]"],
)
