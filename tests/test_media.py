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
                        "sql": "select content, 'png' as output_format, 101 as resize_width from photos"
                    }
                }
            }
        },
    ).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/media/photos/1")
    assert 200 == response.status_code
    image = Image.open(io.BytesIO(response.content))
    assert image.size == (100, 75)
    assert "PNG" == image.format
