from datasette.app import Datasette
import pytest
import httpx


@pytest.mark.asyncio
async def test_media():
    app = Datasette([], memory=True).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/media/type/key")
    assert 200 == response.status_code
    assert "Type=type, Key=key" == response.content.decode("utf8")
