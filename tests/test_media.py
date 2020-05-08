from datasette.app import Datasette
from sqlite_utils import Database
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
    assert "text/plain; charset=utf-8" == response.headers["content-type"]


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
