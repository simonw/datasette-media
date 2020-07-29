from asgiref.testing import ApplicationCommunicator
from datasette.app import Datasette
from sqlite_utils import Database
from PIL import Image
import io
import pathlib
import pytest
import httpx


@pytest.mark.asyncio
async def test_media_filepath(tmpdir):
    filepath = tmpdir / "hello.txt"
    filepath.write_text("hello", "utf-8")
    app = Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-media": {
                    "photos": {"sql": "select '{}' as filepath".format(filepath)}
                }
            }
        },
    ).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/media/photos/key")
    assert 200 == response.status_code
    assert "hello" == response.content.decode("utf8")
    assert "text/plain" == response.headers["content-type"]


@pytest.mark.asyncio
async def test_media_blob(tmpdir):
    app = Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-media": {
                    "text": {
                        "sql": "select 'Hello ' || :key as content, 'text/plain' as content_type"
                    }
                }
            }
        },
    ).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/media/text/key")
    assert 200 == response.status_code
    assert "Hello key" == response.content.decode("utf8")
    assert "text/plain" == response.headers["content-type"]


@pytest.mark.asyncio
async def test_media_content_url(httpx_mock):
    jpeg = pathlib.Path(__file__).parent / "example.jpg"
    httpx_mock.add_response(
        data=jpeg.open("rb").read(), headers={"Content-Type": "image/jpeg"}
    )
    app = Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-media": {
                    "photos": {
                        "sql": "select 'http://example/example.jpg' as content_url"
                    }
                }
            }
        },
    ).app()
    status_code, headers, body = await request(app, "/-/media/photos/1")
    assert 200 == status_code
    image = Image.open(io.BytesIO(body))
    assert image.size == (313, 234)
    assert "JPEG" == image.format


@pytest.mark.asyncio
async def test_media_content_url_transform(httpx_mock):
    jpeg = pathlib.Path(__file__).parent / "example.jpg"
    httpx_mock.add_response(
        data=jpeg.open("rb").read(), headers={"Content-Type": "image/jpeg"},
    )
    app = Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-media": {
                    "photos": {
                        "sql": "select 'http://example/example.jpg' as content_url, 100 as resize_width",
                        "enable_transform": True,
                    }
                }
            }
        },
    ).app()
    status_code, headers, body = await request(app, "/-/media/photos/2?format=PNG")
    assert 200 == status_code
    image = Image.open(io.BytesIO(body))
    assert image.size == (100, 74)
    assert "PNG" == image.format


@pytest.mark.asyncio
async def test_database_option(tmpdir):
    filepath = tmpdir / "hello.txt"
    filepath.write_text("hello2", "utf-8")

    one = str(tmpdir / "one.db")
    two = str(tmpdir / "two.db")

    Database(one)["t"].insert({"hello": 1})
    Database(two)["photos"].insert({"pk": 1, "filepath": str(filepath)})

    app = Datasette(
        [one, two],
        memory=True,
        metadata={
            "plugins": {
                "datasette-media": {
                    "photos": {
                        "sql": "select filepath from photos where pk=:key",
                        "database": "two",
                    }
                }
            }
        },
    ).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/media/photos/1")
    assert 200 == response.status_code
    assert "hello2" == response.content.decode("utf8")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_sql,expected_width,expected_height",
    (
        ("", 313, 234),
        (", 99 as resize_width", 99, 74),
        (", 99 as resize_height", 132, 99),
    ),
)
async def test_sql_resize(extra_sql, expected_width, expected_height):
    jpeg = str(pathlib.Path(__file__).parent / "example.jpg")
    app = Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-media": {
                    "photos": {
                        "sql": "select '{}' as filepath{}".format(jpeg, extra_sql)
                    }
                }
            }
        },
    ).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/media/photos/1")
    assert 200 == response.status_code
    image = Image.open(io.BytesIO(response.content))
    actual_width, actual_height = image.size
    assert (expected_width, expected_height) == (actual_width, actual_height)
    assert "JPEG" == image.format


@pytest.mark.asyncio
async def test_sql_convert_filepath():
    jpeg = str(pathlib.Path(__file__).parent / "example.jpg")
    app = Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-media": {
                    "photos": {
                        "sql": "select '{}' as filepath, 'png' as output_format".format(
                            jpeg
                        )
                    }
                }
            }
        },
    ).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/media/photos/1")
    assert 200 == response.status_code
    image = Image.open(io.BytesIO(response.content))
    assert (313, 234) == image.size
    assert "PNG" == image.format


@pytest.mark.asyncio
async def test_sql_convert_blob(tmpdir):
    jpeg = pathlib.Path(__file__).parent / "example.jpg"
    db_path = tmpdir / "photos.db"
    Database(str(db_path))["photos"].insert(
        {"content": jpeg.open("rb").read(),}
    )
    app = Datasette(
        [db_path],
        metadata={
            "plugins": {
                "datasette-media": {
                    "photos": {
                        "sql": "select content, 'png' as output_format, 100 as resize_width from photos"
                    }
                }
            }
        },
    ).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/media/photos/1")
    assert 200 == response.status_code
    image = Image.open(io.BytesIO(response.content))
    assert image.size == (100, 74)
    assert "PNG" == image.format


@pytest.mark.parametrize(
    "custom_limit,enabled,args,expected_dimensions,expected_format",
    (
        (None, False, {"w": 100}, (313, 234), "JPEG"),
        (None, True, {"w": 100}, (100, 74), "JPEG"),
        (None, True, {"format": "png"}, (313, 234), "PNG"),
        (None, True, {"h": 100}, (133, 100), "JPEG"),
        (None, True, {"h": 3999}, (5349, 3999), "JPEG"),
        (None, True, {"h": 4000}, (313, 234), "JPEG"),
        (4001, True, {"h": 4000}, (5350, 4000), "JPEG"),
    ),
)
@pytest.mark.asyncio
async def test_transform_query_string(
    custom_limit, enabled, args, expected_dimensions, expected_format
):
    jpeg = str(pathlib.Path(__file__).parent / "example.jpg")
    app = Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-media": {
                    "photos": {
                        "sql": "select '{}' as filepath".format(jpeg),
                        "enable_transform": enabled,
                        "max_width_height": custom_limit,
                    }
                }
            }
        },
    ).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/media/photos/1", params=args)
    assert 200 == response.status_code
    image = Image.open(io.BytesIO(response.content))
    assert expected_dimensions == image.size
    assert expected_format == image.format


@pytest.mark.parametrize(
    "path,expected_size",
    [
        ("/-/media/proxied/1", (313, 234)),
        ("/-/media/proxied_transformed/1", (100, 74)),
        ("/-/media/blob/1", (313, 234)),
        ("/-/media/on_disk/1", (313, 234)),
    ],
)
@pytest.mark.asyncio
async def test_content_filename(path, expected_size, httpx_mock):
    jpeg = pathlib.Path(__file__).parent / "example.jpg"
    jpeg_bytes = jpeg.open("rb").read()
    if "proxied" in path:
        httpx_mock.add_response(data=jpeg_bytes, headers={"Content-Type": "image/jpeg"})
    app = Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-media": {
                    "proxied": {
                        "sql": "select 'http://blah/' as content_url, 'x.jpg' as content_filename"
                    },
                    "proxied_transformed": {
                        "sql": "select 'http://blah/' as content_url, 'x.jpg' as content_filename, 100 as resize_width"
                    },
                    "blob": {
                        "sql": "select X'{}' as content, 'x.jpg' as content_filename".format(
                            jpeg_bytes.hex()
                        )
                    },
                    "on_disk": {
                        "sql": "select '{}' as filepath, 'x.jpg' as content_filename".format(
                            jpeg
                        )
                    },
                }
            }
        },
    ).app()
    status_code, headers, body = await request(app, path)
    assert 200 == status_code
    content_disposition = [
        headers[k] for k in headers if k.lower() == "content-disposition"
    ][0]
    assert content_disposition == 'attachment; filename="x.jpg"'
    image = Image.open(io.BytesIO(body))
    assert expected_size == image.size
    assert "JPEG" == image.format


async def request(app, path):
    # Sometimes we can't use httpx.AsyncClient to execute the test, because
    # we've mocked it using httpx_mock - so we do it the harder way instead
    if "?" in path:
        path, query_string = path.split("?", 1)
        query_string = query_string.encode("utf-8")
    else:
        query_string = b""
    scope = {
        "type": "http",
        "http_version": "1.0",
        "method": "GET",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": query_string,
        "headers": [],
    }
    instance = ApplicationCommunicator(app, scope)
    await instance.send_input({"type": "http.request"})
    messages = []
    start = await instance.receive_output(2)
    messages.append(start)
    assert start["type"] == "http.response.start"
    headers = dict([(k.decode("utf8"), v.decode("utf8")) for k, v in start["headers"]])
    status_code = start["status"]
    # Loop until we run out of response.body
    body = b""
    while True:
        message = await instance.receive_output(2)
        messages.append(message)
        assert message["type"] == "http.response.body"
        body += message["body"]
        if not message.get("more_body"):
            break
    return status_code, headers, body
