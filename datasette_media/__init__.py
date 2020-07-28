import asyncio
from datasette import hookimpl
from datasette.utils.asgi import Response, AsgiFileDownload
from concurrent import futures
import httpx
from mimetypes import guess_type
from PIL import Image
import io
from . import utils

transform_executor = None
RESERVED_MEDIA_TYPES = ("transform_threads", "enable_transform")


@hookimpl
def register_routes():
    return [
        (r"/-/media/(?P<media_type>[^/]+)/(?P<key>.+)", serve_media),
    ]


async def serve_media(datasette, request, send):
    global transform_executor
    plugin_config = datasette.plugin_config("datasette-media") or {}
    pool_size = plugin_config.get("transform_threads") or 4
    if transform_executor is None:
        transform_executor = futures.ThreadPoolExecutor(max_workers=pool_size)

    media_type = request.url_vars["media_type"]
    key = request.url_vars["key"]

    config = plugin_config.get(media_type)
    if media_type in RESERVED_MEDIA_TYPES or config is None:
        return Response.html("<h1>Invalid media type</h1>", status=404)
    sql = config.get("sql")
    if sql is None:
        return Response.html("<h1>Missing SQL from configuration</h1>", status=404)
    database = datasette.get_database(config.get("database"))
    results = await database.execute(sql, {"key": key})
    row = results.first()
    if row is None:
        return Response.html("<h1>404 - no results</h1>", status=404)

    # We need filepath or content
    content = None
    content_type = None
    content_url = None
    filepath = None

    row_keys = row.keys()
    if (
        "filepath" not in row_keys
        and "content" not in row_keys
        and "content_url" not in row_keys
    ):
        return Response.html(
            "<h1>404 - SQL must return 'filepath' or 'content' or 'content_url'</h1>",
            status=404,
        )
    if "content" in row_keys:
        content = row["content"]
    elif "content_url" in row_keys:
        content_url = row["content_url"]
    else:
        filepath = row["filepath"]

    # Images are special cases, triggered by a few different conditions
    should_transform = utils.should_transform(row, config, request)
    if should_transform:
        if content is None and content_url:
            async with httpx.AsyncClient() as client:
                response = await client.get(row["content_url"])
                content = response.content
                content_type = response.headers["content-type"]
        image_bytes = content or open(filepath, "rb").read()
        image = await asyncio.get_event_loop().run_in_executor(
            transform_executor,
            lambda: utils.transform_image(image_bytes, **should_transform),
        )
        return utils.ImageResponse(image, format=should_transform.get("format"))
    else:
        # content_url is proxied as a special case
        if content_url:
            client = httpx.AsyncClient()
            async with client.stream("GET", content_url) as response:
                content_type = response.headers["content-type"]
                content_length = response.headers.get("content-length")
                headers = [(b"content-type", content_type.encode("utf-8"))]
                if content_length:
                    headers.append(
                        (b"content-length", str(content_length).encode("utf-8"))
                    )
                await send(
                    {"type": "http.response.start", "status": 200, "headers": headers}
                )
                async for chunk in response.aiter_bytes():
                    await send(
                        {
                            "type": "http.response.body",
                            "body": chunk,
                            "more_body": True,
                        }
                    )
                await send({"type": "http.response.body", "body": b""})
                return
        # Non-image files are returned directly
        if "content_type" in row_keys:
            content_type = row["content_type"]

        if content:
            return Response(
                content, content_type=content_type or "application/octet-stream"
            )
        else:
            return AsgiFileDownload(
                filepath, content_type=content_type or guess_type(filepath)[0]
            )
