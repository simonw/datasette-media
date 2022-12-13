import os

from setuptools import setup

VERSION = "0.5"


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
    project_urls={
        "Issues": "https://github.com/simonw/datasette-media/issues",
        "CI": "https://github.com/simonw/datasette-media/actions",
        "Changelog": "https://github.com/simonw/datasette-media/releases",
    },
    license="Apache License, Version 2.0",
    classifiers=[
        "Framework :: Datasette",
        "License :: OSI Approved :: Apache Software License",
    ],
    version=VERSION,
    packages=["datasette_media"],
    entry_points={"datasette": ["media = datasette_media"]},
    install_requires=["datasette>=0.44", "Pillow>=7.1.2", "httpx>=0.13.3"],
    extras_require={
        "test": [
            "asgiref",
            "pytest",
            "pytest-asyncio",
            "sqlite-utils",
            "pytest-httpx>=0.4.0",
        ],
        "heif": ["pyheif>=0.4"],
    },
    tests_require=["datasette-media[test]"],
)
