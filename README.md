# datasette-media

[![PyPI](https://img.shields.io/pypi/v/datasette-media.svg)](https://pypi.org/project/datasette-media/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-media?include_prereleases&label=changelog)](https://github.com/simonw/datasette-media/releases)
[![CircleCI](https://circleci.com/gh/simonw/datasette-media.svg?style=svg)](https://circleci.com/gh/simonw/datasette-media)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-media/blob/master/LICENSE)

Datasette plugin for serving media based on a SQL query.

Use this when you have a database table containing references to files that you would like to be able to serve to your users.

## Installation

Install this plugin in the same environment as Datasette.

    $ pip install datasette-media

## Usage

You can use this plugin to configure Datasette to serve static media based on SQL queries to an underlying database table.

Media will be served from URLs that start with `/-/media/`. The full URL to each media asset will look like this:

    /-/media/type-of-media/media-key

`type-of-media` will correspond to a configured SQL query, and might be something like `photo`. `media-key` will be an identifier that is used as part of the underlying SQL query to find which file should be served.

### Serving static files from disk

The following ``metadata.json`` configuration will cause this plugin to serve files from disk, based on queries to a database table called `apple_photos`:

```json
{
    "plugins": {
        "datasette-media": {
            "photo": {
                "sql": "select filepath from apple_photos where uuid=:key"
            }
        }
    }
}
```

A request to `/-/media/photo/CF972D33-5324-44F2-8DAE-22CB3182CD31` will execute the following SQL query:

```sql
select filepath from apple_photos where uuid=:key
```

The value from the URL -  in this case `CF972D33-5324-44F2-8DAE-22CB3182CD31` - will be passed as the `:key` parameter to the query.

The query returns a `filepath` value that has been read from the table. The plugin will then read that file from disk and serve it in response to the request.

See [photos-to-sqlite](https://github.com/dogsheep/photos-to-sqlite) for an example of an application that can benefit from this plugin.
