from datasette.app import Datasette
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
